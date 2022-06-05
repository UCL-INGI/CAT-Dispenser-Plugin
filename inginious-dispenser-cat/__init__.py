# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from cmath import nan
import os 
import json
import requests

from collections import OrderedDict
from flask import send_from_directory
from datetime import datetime

from inginious.common.base import id_checker
from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.task_dispensers import TaskDispenser
from inginious.frontend.accessible_time import AccessibleTime

__version__ = "0.1.dev0"

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
PATH_TO_TEMPLATES = os.path.join(PATH_TO_PLUGIN, "templates")
PATH_TO_TASKS = "/home/lethblak/Unif/Memoire/INGInious/INGInious/tasks/"
MYIP="127.0.0.1"

class StaticMockPage(INGIniousPage):
    def GET(self, path):
        return send_from_directory(os.path.join(PATH_TO_PLUGIN, "static"), path)

    def POST(self, path):
        return self.GET(path)

class ImportTasks(INGIniousPage):
    def GET(self,courseidfrom,courseid):
        self.database.cat_info.delete_many({'courseid':courseid})
        self.database.cat_info.insert_one({'courseidfrom':courseidfrom,'courseid':courseid})

        command = "cp -nr " + PATH_TO_TASKS + str(courseidfrom) +"/*" + " " + PATH_TO_TASKS + str(courseid) #cp -nr <courseidfrom>/* <courseid>
        ret = os.system(command)

        if ret == 0:
            return "Successfully imported"
        else:
            return "Error in import, please verify your course id"

class ResetTasks(INGIniousPage):
    def GET(self,course_id,username):
        date_archive = str(datetime.now())
        for line in self.database.user_tasks.find({'username':username,'courseid':course_id}):
            line['date'] = date_archive
            self.database.user_tasks_archive.insert_one(line)
        self.database.user_tasks.delete_many({'username':username,'courseid':course_id})

        for line in self.database.submissions.find({'username':username,'courseid':course_id}):
            line['date'] = date_archive
            self.database.submissions_archive.insert_one(line)
        self.database.submissions.delete_many({'username':username,'courseid':course_id})

        for line in self.database.cat_score.find({'username':username,'courseid':course_id}):
            line['date'] = date_archive
            self.database.cat_score_archive.insert_one(line)
        self.database.cat_score.delete_many({'username':username,'courseid':course_id})
        return "OK"
    
class CatDispenser(TaskDispenser):
    def __init__(self, task_list_func, dispenser_data, database, courseId):
        '''
        :param task_list_func: a function returning a dictionary with filesystem taskid as keys and task objects as values
        :param dispenser_data: the dispenser data as written in course.yaml
        '''
        self.database = database
        self.course_id = courseId
        self.original_course = -1

        cat_info = self.database.cat_info.find({"courseid":self.course_id})
        i = 0
        for result in cat_info:
            self.original_course = result['courseidfrom']
            i += 1

        if i == 0: # no info stores => tasks of his own course
            self.original_course = self.course_id
        
        self._task_list_func = task_list_func
        self._data = dispenser_data
        self.score = -1
        self.final_score = False
        self.username = "None"

    @classmethod
    def get_id(cls):
        '''
        :return: a unique id for the task dispenser
        '''
        return "cat_dispenser"

    @classmethod
    def get_name(cls, language):
        '''
        :param language: the user language
        :return: a human readable name for the task dispenser
        '''
        return "Computerized Adapative Testing dispenser"

    def get_dispenser_data(self):
        try:
            datas = self._data.copy()
        except:
            return self._data
        else:
            return datas

    def __array_to_str_json(self,array):
        strJSON = "["
        for i in range(len(array)):
            line = "["
            for j in range(len(array[i])):
                line += str(array[i][j]) + ","
            line = line[:-1]                #remove last ,
            line += "]"
            strJSON += line + ","
        strJSON = strJSON[:-1] + "]"        #remove last , and add ]
        return strJSON
    
    def get_users(self):
        users = []
        for val in self.database.user_tasks.find({'courseid':self.original_course}):
            user = val['username']
            if(user not in users):
                users.append(user)
        return(users)

    def __send_data_to_r(self):
        users = self.get_users()
        tasks = self.get_dispenser_data()
        users_datas = []
        for user in users :
            user_data = []
            for task in tasks :
                grade = -1
                for val in self.database.user_tasks.find({'courseid':self.original_course,'username':user,'taskid':task}):
                    if val['tried'] > 0:
                        if val['succeeded']:
                            grade = 1
                        else:
                            grade = 0
                user_data.append(grade)
            isOnlyNA = True
            for gradeCheck in user_data:
                if gradeCheck != -1 : isOnlyNA = False
            if not isOnlyNA:
                users_datas.append(user_data)
        strJSON = self.__array_to_str_json(users_datas)
        newHeaders = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        requests.post("http://"+MYIP+":8766/newExam",data=json.dumps({'data': strJSON,"index":self.course_id}),headers=newHeaders)

    '''
    Quand on arrive sur la liste des exo ET que on applique les changements
    '''
    def render_edit(self, template_helper, course, task_data):
        '''
        :param template_helper: the template_helper singleton
        :param course: the WebAppCourse object
        :param task_data: a helper dictionary containing the human-readable name and download urls
        :return: HTML code for the task list edition page
        '''
        self.__send_data_to_r()
        return template_helper.render("admin/task_list_edit.html", template_folder=PATH_TO_TEMPLATES, course=course,
                                    dispenser_data=self._data, tasks=task_data)

    def render(self, template_helper, course, tasks_data, tag_list):
        '''
        :param template_helper: the template_helper singleton
        :param course:  the WebAppCourse object
        :param tasks_data: a helper dict containing achievements status for each task
        :param tag_list: the course tag list to help filtering the tasks (can be ignored)
        :return: HTML code for the student task list page
        '''
        score = ""
        button_reset = "None"
        if self.score != -1 and not self.final_score:
            score = "Actual Grade: " + str(round(self.score, 2)) + " %"
        elif self.score != -1 and self.final_score:
            #button_reset = "block"                             UNCOMMENT FOR A RESET BUTTON (INDIVIDUAL)
            score = "Final Grade: "  + str(round(self.score, 2)) + " %"

        datas = {"data":self._data,"score":score,"reset":button_reset,"username":self.username}
        
        return template_helper.render("student/task_list.html", template_folder=PATH_TO_TEMPLATES, course=course,
                                      tasks=self._task_list_func(), tasks_data=tasks_data, tag_filter_list=tag_list,
                                      dispenser_data=datas)

    def check_dispenser_data(self, dispenser_data):
        '''
        Checks the dispenser data as formatted by the form from render_edit function
        :param dispenser_data: dispenser_data got from the web form (dispenser_structure_ js function)
        :return: A tuple (bool, List<str>). The first item is True if the dispenser_data got from the web form is valid
        The second takes a list of string containing error messages
        '''
        disp_task_list = json.loads(dispenser_data)
        valid = any(set([id_checker(taskid) for taskid in disp_task_list]))
        errors = [] if valid else ["Wrong task ids"]
        return disp_task_list if valid else None, errors

    def __get_task_name(self,id):
        tasks = self.get_dispenser_data()
        return tasks[id-1]

    def __get_tasks_name(self,tasks_ids):
        tasks = []
        for id in tasks_ids:
            tasks.append(self.__get_task_name(id))
        return tasks

    def __get_task_id(self,task):
        i = 1
        tasks = self.get_dispenser_data()
        for t in tasks:
            if task == t:
                return i
            i = i +1
        return -1

    def __get_already_answered(self,username):
        tasks_ids = []
        grades = []
        for val in self.database.user_tasks.find({'courseid':self.course_id,'username':username}):
            task = val['taskid']
            taskid = self.__get_task_id(task)
            if taskid != -1 and val['tried'] != 0:
                tasks_ids.append(taskid)
                grades.append(val['grade']/100)
        if len(tasks_ids) == 0:
            return([],-1)
        return (tasks_ids,grades)

    def get_user_task_list(self, usernames):
        '''
        Returns the task list as seen by the specified users
        :param usernames: the list of users usernames who the user task list is needed for
        :return: a dictionary with username as key and the user task list as value
        '''
        values = {}
        for user in usernames:
            try:
                self.username = user
                questions = self.__get_already_answered(user)
                questions_id = questions[0]
                responses = questions[1]

                newHeaders = {'Content-type': 'application/json', 'Accept': 'text/plain'}
                response = requests.post("http://"+MYIP+":8766/nextQuestion",data=json.dumps({'itemBankID':self.course_id,'alreadyAnswered':questions_id,'responseList':responses}),headers=newHeaders)
                responseJSON = json.loads(response.text)

                nextQuestion = responseJSON["index"][0]
                self.score = responseJSON["score"][0]

                if nextQuestion == -1: #No new question to ask
                    self.final_score = True
                    temp = self.__get_tasks_name(questions_id)
                    values[user] = temp
                else :
                    self.final_score = False
                    questions_id.append(nextQuestion)
                    values[user] = self.__get_tasks_name(questions_id)

                self.database.cat_score.delete_many({'username':user,"courseid":self.course_id})
                self.database.cat_score.insert_one({'username':user,"courseid":self.course_id,'score':self.score,"finalscore":self.final_score,"nombrequestions":len(values[user])})
            except:
                values[user] = []
        return values

    def get_ordered_tasks(self):
        """ Returns a serialized version of the tasks structure as an OrderedDict"""
        tasks = self._task_list_func()
        return OrderedDict([(taskid, tasks[taskid]) for taskid in self._data if taskid in tasks])

    def get_task_order(self, taskid):
        """ Get the position of this task in the course """
        tasks = self._data
        if taskid in tasks:
            return tasks.index(taskid)
        else:
            return len(tasks)
    
def task_accessibility(course, task, default_value, database, user_manager):
    dispenser = course.get_task_dispenser().get_id()
    if dispenser != "cat_dispenser":
        return default_value
    courseid = course.get_id()
    username = user_manager.session_username()
    taskid = task.get_id()
    submissions = database.user_tasks.find({'courseid':courseid,'taskid':taskid,'username':username})
    nbr_submissions = 0
    tried = False
    for sub in submissions:
        nbr_submissions += 1
        if sub['tried'] != 0:
            tried = True
    if nbr_submissions > 0 and tried:
        return AccessibleTime(False)
    else:
        return AccessibleTime(True)

def init(plugin_manager, course_factory, client, plugin_config):
    plugin_manager.add_page('/plugins/disp_cat/static/import_tasks/<courseidfrom>/<courseid>',ImportTasks.as_view('catdispensertest'))
    plugin_manager.add_page('/plugins/disp_cat/static/reset_tasks/<course_id>/<username>',ResetTasks.as_view('catdispenserreset'))
    plugin_manager.add_page('/plugins/disp_cat/static/<path:path>', StaticMockPage.as_view("catdispenserstaticpage"))
    plugin_manager.add_hook("javascript_header", lambda: "/plugins/disp_cat/static/admin.js")
    plugin_manager.add_hook("javascript_header", lambda: "/plugins/disp_cat/static/student.js")
    plugin_manager.add_hook('task_accessibility', lambda course, task, default: task_accessibility(course, task, default,
                                                                                                 plugin_manager.get_database(),
                                                                                                 plugin_manager.get_user_manager()))
    course_factory.add_task_dispenser(CatDispenser)