#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import os.path
import xml.dom.minidom
import MySQLdb
import sys
import random

global oneInNum
global project_name
project_name='test0720'
global db
global idNum
idNum = 0
global idNumSelect

def con_db():
    global project_name
    hostName = "xxx.xx.xxx.xx"
    userName = "xxxx"
    passWord = "xxxxxxx"
    #dataBase = "ground_truth"
    dataBase = project_name
    charset = "utf8"
    db = MySQLdb.connect("%s"%(hostName), "%s"%(userName), "%s"%(passWord), "%s"%(dataBase), charset='utf8' )
    
    global oneInNum
    oneInNum = 20
    global idNum
    idNum = 0
    
    return db

db = con_db()
def setProjectName(projectNameNew):
    global project_name,db
    project_name_old=project_name
    #project_name = str(projectNameNew)
    #cursor = db.cursor()
    #cursor_execute("use %s"%(projectName))
    db.close()
    #message have two informations:the status of project_name,and True/False(to introduct the following action)
    message = []
    try:
        project_name = str(projectNameNew)
        db=con_db()
        message.append("set project_name=%s success.project_name=%s"%(projectNameNew,project_name))
        message.append(True)
    except Exception as e:
        print e
        #message=e
        #message="set project_name=%s failed."%(projectNameNew)
        project_name=project_name_old
        message.append("set project_name=%s failed.project_name=%s"%(projectNameNew,project_name))
        message.append(False)
        db=con_db()
    print message
    return message

#set the verify rate
def setOneInNum(newNum):
    global oneInNum
    oldNum = oneInNum
    try:
        oneInNum = int(newNum)
    except Exception as e:
        print e
        oneInNum = oldNum
        return [oneInNum, False]
    return [oneInNum, True]

##insert the label to databases.
def insert2sql(info):
    #info:[(id+ '. '+ text), label]
    global project_name 
    global db
    global idNum
    #connect xml databases to upload xml file.
    cursor = db.cursor()
    updateNum = int(info[0].split('.')[0])
    label = info[1]
    sql = "UPDATE %stext SET label = '%s' WHERE id = %d" % (project_name, unicode(label), updateNum)
    print("%s"%(sql)) 
    try:
        cursor.execute(sql)
    except Exception as e:
        print sql
        print e
        cursor.execute(sql)
    
    db.commit()  

def cursor_execute(sqlstr):
    global db
    cursor = db.cursor()
    content=None
    try:
        cursor.execute(sqlstr)
        content = cursor.fetchone()
    except Exception as e:
        print sqlstr
        print e
    return content

#this function isn't used in labelTxt 
def xmlfromsql(xmlpath):
    global project_name
    global db
    
    cursor = db.cursor()
    
    filename = str(xmlpath).split('\\')[-1]
    image_name = filename[:-4]
    #print image_name 
    sql = "SELECT xml_content FROM %sxml WHERE image_name = '%s'"%(project_name,image_name)
    #xml_content = cursor_execute(sql)
    xml_content=cursor_execute(sql)
    #print "xml content:",xml_content
    if xml_content == None:
        return
    else:
        if not os.path.isfile(xmlpath):     
            fout = open(xmlpath,'wb')
            fout.write("")
            fout.write(xml_content[0])
            fout.close()
            print "The xml file have downloaded form database."
        else:
            return
    
    db.commit()
    #cursor.close()

def resetIdNum():
    global idNum
    idNum = 0

def imagefromsql(dirpath, softwareMode = 'resume'):
    global project_name
    global db
    global idNum
    global idNumSelect
    
    #This is verify mode to check the correct rate.
    if softwareMode == 'verify':
        global oneInNum
        #cursor_execute("SELECT image_name FROM pngtry WHERE (is_marking = 'done' and if_verify = 'no') LIMIT %d"% oneInNum)
        cursor_content = cursor_execute("SELECT count(*) FROM %stext WHERE (is_marking = 'done' and if_verify = 'no') "%(project_name))
        remainNum = cursor_content[0]
        if remainNum == 0:
            print "All texts have been verified."
            return
        elif remainNum > 0 and remainNum < oneInNum:
            oneInNum = remainNum
        
        cursor = db.cursor()
        cursor.execute("SELECT id FROM %stext WHERE (is_marking = 'done' and if_verify = 'no') ORDER BY id LIMIT 20"%(project_name))
        idTuple = tuple(cursor.fetchall())
        print"id tuple:", idTuple
        select = random.randint(0, oneInNum-1)
        #idTuple is two-dimensional tuple
        idNumSelect = idTuple[select][0]
        cursor = cursor_execute("SELECT text_content,label FROM %stext WHERE id = %d"%(project_name, idNumSelect))
        text_content = cursor[0]
        label = cursor[1]

        idNum = idNumSelect + 1
    #This is browse mode, which can get texts from id == 1.
    elif softwareMode == 'no_resume':
        
        cursor = cursor_execute("SELECT id FROM %stext ORDER BY id DESC LIMIT 1"%(project_name))
        lastImgNum = cursor[0]
        if lastImgNum < idNum:
            print "No more picture!"
            return
        
        if idNum == 0:
            idNum += 1
        cursor = cursor_execute("SELECT id, text_content, label FROM %stext WHERE id >= %d ORDER BY id LIMIT 1"%(project_name, idNum))
        idNum = cursor[0]
        text_content = cursor[1]
        label = cursor[2]
    
        idNum += 1
    
    #This is marking mode, to add label on image.    
    elif softwareMode == 'resume':
        cursor = cursor_execute("SELECT count(*) FROM %stext"%(project_name))
        allImgNum = cursor[0]
        cursor = cursor_execute("SELECT count(*) FROM %stext WHERE is_marking = 'no'"%(project_name))
        remainNum = cursor[0]
        markedNum = allImgNum - remainNum
        print "%d text have been marked."% markedNum
        if remainNum == 0:
            print "No more text!"
            return
        #cursor_execute("SELECT image_name FROM pngtry WHERE is_marking ='no' LIMIT 1")
        cursor = cursor_execute("SELECT id FROM %stext WHERE is_marking ='no' ORDER BY id LIMIT 1"%(project_name))
        idNum = cursor[0]
        cursor = cursor_execute("SELECT text_content, label FROM %stext WHERE id = %d"%(project_name, idNum))
        text_content = cursor[0]
        label = cursor[1]
            
        cursor_execute("UPDATE %stext SET is_marking = 'done' WHERE id = %d"%(project_name, idNum))
        print "The is_marking status has update to 'done' in database."
        idNum += 1
            
    db.commit()
    #cursor.close()
    return [(str(idNum - 1)+'. '+text_content), label]

def veriResult(result):
    global project_name
    global db
    global idNumSelect
    global oneInNum
    
    cursor = db.cursor()
    cursor.execute("SELECT id FROM %stext WHERE (is_marking = 'done' and if_verify = 'no') ORDER BY id LIMIT 20"%(project_name))
    idNumListTuple = list(tuple(cursor.fetchall()))
    if len(idNumListTuple) == 0:
        return
    idNumList = []
    for i in range(0,oneInNum):
        idNumList.append(idNumListTuple[i][0])
    print"id list:", idNumList 
    cursor_execute("UPDATE %stext SET if_verify = '%s' WHERE id = %d"%(project_name,result, idNumSelect))

    print "idNumSelect: ", idNumSelect
    idNumList.remove(idNumSelect)
    print "id list2:", idNumList
    for i in idNumList:
        #cursor_execute("UPDATE pngtry SET if_verify = 'jump' WHERE image_name = '%s'"% imgname_list[i][0])
        cursor_execute("UPDATE %stext SET if_verify = 'jump' WHERE id = %d"%(project_name,i))
    db.commit()
    #cursor.close()

def veriCount():
    global project_name
    global db
    #list :rightNum, wrongNum, rate,veriNum,tabelVeriNum, allImgNum, veriRate
    cursor = db.cursor()
    resultList = ()
    cursor = cursor_execute("SELECT count(*) FROM %stext WHERE if_verify = '%s'"%(project_name, 'is_verified_right'))
    rightNum = cursor[0]
    #resultList.append(rightNum)
    cursor = cursor_execute("SELECT count(*) FROM %stext WHERE if_verify = '%s'"%(project_name, 'is_verified_wrong'))
    wrongNum = cursor[0]
    #resultList.append(wrongNum)
    veriNum = rightNum + wrongNum
    rate = float(rightNum) / float(veriNum)
    rate = '%.3f'% rate
    #resultList.append(rate)
    #resultList.append(veriNum)
    cursor = cursor_execute("SELECT count(*) FROM %stext WHERE if_verify != 'no'"%(project_name))
    tabelVeriNum = cursor[0]
    #resultList.append(tabelVeriNum)
    cursor = cursor_execute("SELECT count(*) FROM %stext WHERE is_marking = 'done'"%(project_name))
    allImgNum = cursor[0]
    #resultList.append(allImgNum)
    veriRate = float(tabelVeriNum) / float(allImgNum)
    veriRate = '%.2f'% veriRate
    #resultList.append(veriRate)
    resultList = (rightNum, wrongNum, rate,veriNum,tabelVeriNum, allImgNum, veriRate)
    
    db.commit()
    #cursor.close()
    return resultList

def markCount():
    
    global project_name
    global db
    #list :markNum, allNum, markRate
    cursor = db.cursor()
    resultList = ()
    cursor = cursor_execute("SELECT count(*) FROM %stext WHERE is_marking = 'done'"%(project_name))
    markNum = cursor[0]
    cursor = cursor_execute("SELECT count(*) FROM %stext "%(project_name))
    allNum = cursor[0]
    markRate = float(markNum) / float(allNum)
    markRate = '%.2f'% markRate
    resultList = (markNum, allNum, markRate)
    return resultList

#The following three functions are not used in labelTxt
def delfile():
    global db
    db.close()

    delList = []
    delDir = "C:\markimage"
    if os.path.isdir(delDir):
        delList = os.listdir(delDir)

        for f in delList:
            filePath = os.path.join( delDir, f )
            if os.path.isfile(filePath):
                os.remove(filePath)
            elif os.path.isdir(filePath):
                shutil.rmtree(filePath,True)
        os.rmdir(delDir)
        print "Directory: " + delDir +" was removed!"
                
    delList = []
    delDir = "C:\markxml"
    if os.path.isdir(delDir):
        delList = os.listdir(delDir)

        for f in delList:
            filePath = os.path.join( delDir, f )
            if os.path.isfile(filePath):
                os.remove(filePath)
            elif os.path.isdir(filePath):
                shutil.rmtree(filePath,True)
        os.rmdir(delDir)
        print "Directory: " + delDir +" was removed!"

#This function can download all images refer the input projectName
#Both parameters are entered from the software window
def allImgFromDb(projectDirPath):
    
    global db
    cursor = db.cursor()
    global project_name
    projectName = project_name
    #make a directory "projectnameimg"
    imgDirPath = os.path.join(projectDirPath, '%simg'%projectName)
    isExists = os.path.exists(imgDirPath)
    if not isExists:
        os.makedirs(imgDirPath)
        print "%simg folder is created successfully."%projectName
    
    #get the img count in database
    cursor.execute("SELECT count(*) FROM %simg"% (projectName))
    imgNum = cursor.fetchone()[0]
    print "The project have %d img."% imgNum
    #get the img_raw_data refer to idNum
    idNum = 1
    
    #for i in range(0, imgNum):
    for i in range(0, imgNum):
        
        sql = "SELECT id, raw_data FROM %simg WHERE id >= %d ORDER BY id LIMIT 1"%(projectName, idNum)
        cursor.execute(sql)
        content = cursor.fetchall()
        #content: ((id, raw_data), )
        idNum = content[0][0]
        
        #if there isn't content, len(content) = 0
        if len(content) < 1:
            print "Id %d imgdatabese have no content."% idNum
        else:
            #get the image_name to set the imgfile name.
            cursor.execute("SELECT image_name FROM %simg WHERE id = %d"% (projectName, idNum))
            image_name = cursor.fetchone()[0]
            imgfile = str(image_name) + '.png'
            imgPath = os.path.join(imgDirPath, imgfile)
            #print "imgfile", imgfile
            if not os.path.isfile(imgPath):
                fout = open(imgPath,'wb')
                #print "os.path.join('%simg'%project_name, imgfile)", os.path.join('%sxml'%project_name, xmlfile)
                fout.write(content[0][1])
                fout.close()
                print "Id %d img file have been downloaded form database."% idNum
        idNum += 1
    db.commit()
    cursor.close()
    return imgDirPath
    
#This function can download all xml file refer the input projectName
#Both parameters are entered from the software window
def allXmlFromDb(projectDirPath):
    
    global db
    cursor = db.cursor()
    global project_name
    projectName = project_name
    
    #make a directory "projectnamexml"
    xmlDirPath = os.path.join(projectDirPath, '%sxml'%projectName)
    isExists = os.path.exists(xmlDirPath)
    if not isExists:
        os.makedirs(xmlDirPath)
        print "%sxml folder is created successfully."%projectName
    
    #get the xml file count in database
    #cursor.execute("SELECT count(*) FROM %sxml"% (projectName))
    print "SELECT count(*) FROM %sxml"% (projectName)
    cursor.execute("SELECT count(*) FROM %sxml"% (projectName))
    xmlNum = cursor.fetchone()[0]
    print "The project have %d xml."% xmlNum
    #get the xml_content refer to idNum
    idNum = 1
    
    for i in range(0, xmlNum):
    #for i in range(0, 1):
        
        sql = "SELECT id, xml_content FROM %sxml WHERE id >= %d ORDER BY id LIMIT 1"%(projectName, idNum)
        cursor.execute(sql)
        content = cursor.fetchall()
        #content: ((id, xml_content), )
        idNum = content[0][0]
        print "idNum", idNum
        
        #if no content, len(content) = 0
        if len(content) < 1:
            print "Id %d xmldatabese have no content."% idNum
        else:
            #get the image_name to set the xmlfile name.
            cursor.execute("SELECT image_name FROM %sxml WHERE id = %d"% (projectName, idNum))
            image_name = cursor.fetchone()[0]
            xmlfile = str(image_name) + '.xml'
            #print "xmlfile", xmlfile
            if not os.path.isfile(xmlfile):
                fout = open(os.path.join(xmlDirPath, xmlfile),'wb')
                #print "os.path.join('%sxml'%project_name, xmlfile)", os.path.join('%sxml'%project_name, xmlfile)
                fout.write(content[0][1])
                fout.close()
                print "Id %d xml file have downloaded form database."% idNum
        idNum += 1
    db.commit()
    cursor.close()
    return xmlDirPath

#imagefromsql(r'D:\file\try\trydown_png', True)
