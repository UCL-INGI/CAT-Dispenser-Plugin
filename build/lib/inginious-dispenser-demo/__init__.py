# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from cmath import nan
import os 
import json
import random
import requests


from collections import OrderedDict
from flask import send_from_directory

from inginious.common.base import id_checker
from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.task_dispensers import TaskDispenser

__version__ = "0.1.dev0"

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
PATH_TO_TEMPLATES = os.path.join(PATH_TO_PLUGIN, "templates")
#MYIP="109.136.115.168"
MYIP="127.0.0.1"

class StaticMockPage(INGIniousPage):
    def GET(self, path):
        return send_from_directory(os.path.join(PATH_TO_PLUGIN, "static"), path)

    def POST(self, path):
        return self.GET(path)


class CatDispenser(TaskDispenser):

    def __init__(self, task_list_func, dispenser_data):
        '''
        :param task_list_func: a function returning a dictionary with filesystem taskid as keys and task objects as values
        :param dispenser_data: the dispenser data as written in course.yaml
        '''
        self._task_list_func = task_list_func
        self._data = dispenser_data
        self.originalCourse = "CatRandom30"
        self.name = "CatDemo1"
        self.score = -1
        self.finalScore = False

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
        return "Cat task dispenser"

    def add_database(self,database):
        self.database = database
        return

    def get_dispenser_data(self):
        return self._data

    def __arrayToStrJSON(self,array):
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
    
    def getUsers(self):
        users = []
        for val in self.database.user_tasks.find({'courseid':self.originalCourse}):
            user = val['username']
            if(user not in users):
                users.append(user)
        return(users)
    
    def getTasks(self):
        tasks = []
        for val in self.database.user_tasks.find({'courseid':self.originalCourse}):
            task = val['taskid']
            if(task not in tasks):
                tasks.append(task)
        return(self.get_dispenser_data())

    def __sendDataToR(self):
        users = self.getUsers()
        tasks = self.getTasks()
        usersDatas = []
        for user in users :
            userData = []
            for task in tasks :
                grade = -1
                for val in self.database.user_tasks.find({'courseid':self.originalCourse,'username':user,'taskid':task}):
                    if val['tried'] > 0:
                        if val['succeeded']:
                            grade = 1
                        else:
                            grade = 0
                userData.append(grade)
            isOnlyNA = True
            for gradeCheck in userData:
                if gradeCheck != -1 : isOnlyNA = False
            if not isOnlyNA:
                usersDatas.append(userData)
        strJSON = self.__arrayToStrJSON(usersDatas)
        newHeaders = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post("http://"+MYIP+":8766/newExam",data=json.dumps({'data': strJSON,"index":self.name}),headers=newHeaders)

    '''def __deleteDataToR(self):
        newHeaders = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.delete("http://"+MYIP":8766/deleteItemBank",data=json.dumps({'data': self.name}),headers=newHeaders)'''

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
        self.__sendDataToR()
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
        if self.score != -1 and not self.finalScore:
            score = "Actual Grade: " + str(round(self.score, 2)) + " %"
        elif self.score != -1 and self.finalScore:
            score = "Final Grade: "  + str(round(self.score, 2)) + " %"
        datas = {"data":self._data,"score":score}
        
        return template_helper.render("student/task_list.html", template_folder=PATH_TO_TEMPLATES, course=course,
                                      tasks=self._task_list_func(), tasks_data=tasks_data, tag_filter_list=tag_list,
                                      dispenser_data=datas)

    '''
    C'EST ICI QUE LE CODE PASSE QUAND ON APPLIQUE LES CHANGEMENTS
    '''
    @classmethod
    def check_dispenser_data(cls, dispenser_data):
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

    def __getTaskName(self,id):
        tasks = self.get_dispenser_data()
        return tasks[id-1]

    def __getTasksName(self,tasksIds):
        tasks = []
        for id in tasksIds:
            tasks.append(self.__getTaskName(id))
        return tasks

    def __getTaskId(self,task):
        i = 1
        tasks = self.get_dispenser_data()
        for t in tasks:
            if task == t:
                return i
            i = i +1
        return -1

    def __getAlreadyAnswered(self,username):
        tasksIds = []
        grades = []
        for val in self.database.user_tasks.find({'courseid':self.name,'username':username}):
            task = val['taskid']
            taskId = self.__getTaskId(task)
            if taskId != -1 and val['tried'] != 0:
                tasksIds.append(taskId)
                grades.append(val['grade']/100)
        if len(tasksIds) == 0:
            return(-1,-1)
        return (tasksIds,grades)

    def get_user_task_list(self, usernames):
        '''
        Returns the task list as seen by the specified users
        :param usernames: the list of users usernames who the user task list is needed for
        :return: a dictionary with username as key and the user task list as value
        '''
        ret2 = {}
        for user in usernames:
            questions = self.__getAlreadyAnswered(user)
            questionsId = questions[0]
            responses = questions[1]
            newHeaders = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            response = requests.post("http://"+MYIP+":8766/nextQuestion",data=json.dumps({'itemBankID':self.name,'alreadyAnswered':questionsId,'responseList':responses}),headers=newHeaders)
            responseJSON = json.loads(response.text)
            nextQuestion = responseJSON["index"][0]
            self.score = responseJSON["score"][0]
            if nextQuestion == -1:
                questionsId = []
                self.finalScore = True
            else :
                questionsId = [nextQuestion]       # Only last question displayed
                #questionsId.append(nextQuestion)  # All Questions displayed
            ret2[user] = self.__getTasksName(questionsId)
        return ret2

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

def init(plugin_manager, course_factory, client, plugin_config):
    # TODO: Replace by shared static middleware and let webserver serve the files
    plugin_manager.add_page('/plugins/disp_cat/static/<path:path>', StaticMockPage.as_view("catdispenserstaticpage"))
    plugin_manager.add_hook("javascript_header", lambda: "/plugins/disp_cat/static/admin.js")
    plugin_manager.add_hook("javascript_header", lambda: "/plugins/disp_cat/static/student.js")
    course_factory.add_task_dispenser(CatDispenser)