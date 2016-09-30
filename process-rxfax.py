#
# Fax reception Python
# 2011-06-30
# David Laperle @ RSS
#

import sys                            # import the sys module for argv
import os                              # import the os modules
import time
import smtplib, email, datetime
import glob
import math
import string
from email.Encoders import encode_base64
from email.MIMEMultipart import MIMEMultipart
from email.MIMEAudio import MIMEAudio
from email.Header import Header
from email.MIMEText import MIMEText
from datetime import *
from freeswitch import *

## EDIT THESE VARIABLES TO MATCH YOUR NEEDS:

tiff2pscmd = '/usr/bin/tiff2ps'      # location of tiff2ps
tiff2pdfcmd = '/usr/bin/tiff2pdf'      # location of tiff2pdf
ncftpputcmd = '/usr/local/bin/ncftpput' # location of ncftpput
lprcmd = '/usr/bin/lpr'              # location of lpr
convertcmd = '/usr/bin/convert'      # location of convert
incomingfaxes = '/tmp/'              # change this to where your .tiffs are saved by mod_fax, trailing slash required
ftphost = 'host'
ftpuser = 'user'
ftppass = 'pass'
today = date.today().strftime("%Y%m%d")
tiff2psoptions = '-a -O '              # command line options go here 
logfile = "/usr/local/freeswitch/log/rxfax_" + today + ".log"

def sendErrorToMail(subject,reason):
    email_from = "from@domain.com"
    email_rcpt = "to@domain.com"
    msg = MIMEMultipart('alternative')
    msg.set_charset('utf-8')
    sub = Header(subject,'utf-8')
    msg['Subject'] = sub
    msg['From'] = email_from
    msg['To'] = email_rcpt
    textv = reason
    part1 = MIMEText(textv,'plain','utf-8')
    msg.attach(part1)
    mailer = smtplib.SMTP("server.smtp.com",25)
    mailer.sendmail(email_from, email_rcpt, msg.as_string())
    mailer.quit()

def writeToLog(session,msg):
    global logfile
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    uuid = session.getVariable("uuid")
    towrite = now + " " + uuid + " " + msg + "\n"
    fh = open(logfile,"a")
    fh.write(towrite)
    fh.close()

def handler(session, args):

    #get required variables
    the_uuid = session.getVariable("uuid")
    the_recipient = session.getVariable("recipient")
    the_caller = session.getVariable("caller_id_number")
    the_dest = session.getVariable("destination_number")

    writeToLog(session,"Incoming Fax from " + the_caller)
    #test if FTP works before proceeding
    error = os.system(ncftpputcmd + " -m -u " + ftpuser + " -p " + ftppass + " " + ftphost + " / /usr/local/freeswitch/scripts/testfile.txt ")
    if error == 0:
        writeToLog(session,"Fax reception in progress ...")
        #answer the phone, save the fax file in .tiff format.    
        session.answer()
        session.execute("playback", "silence_stream://2000")
        session.execute("rxfax", incomingfaxes + "rxfax-" + the_uuid + ".tiff")
        writeToLog(session,"Fax reception done: " + incomingfaxes + "rxfax-" + the_uuid + ".tiff")
        # We split the TIFF so we can have different page size within the same fax
        writeToLog(session,"Splitting TIFF")
        os.system(convertcmd + " " + incomingfaxes + "rxfax-" + the_uuid + ".tiff " + incomingfaxes + "rxfax-" + the_uuid + "_%04d.tiff")
        # We send the TIFF to ps directly to the printer
        writeToLog(session,"Sending Fax to printer")
        pages = glob.glob(incomingfaxes + "rxfax-" + the_uuid + "_*.tiff")
        pages.sort()
        for page in pages:
            # For each page we want to be able to determine the height, but depending on the y-resolution, it can change a little, so we do a little math, to always put the height on the same resolution
            val = 0
            p = os.popen('/usr/bin/identify -format \"%h\" ' + page)
            height = p.readline()
            p.close()
            r = os.popen('/usr/bin/identify -format \"%y\" ' + page)
            resolution = r.readline()
            r.close()
            ardpi = string.split(resolution)
            dpi = int(ardpi[0])
            if dpi != 196:
                if dpi > 196:
                    val = (dpi/196)*int(height)
                else:
                    val = (196/dpi)*int(height)
            else:
                val = int(height)
            if int(val) > 2300:
                writeToLog(session,page + " is LEGAL!")
                os.system(tiff2pscmd + " -h14 " + page + " | " + lprcmd + " -P myprinter -o media=legal -o fitplot=true")
            else:
                writeToLog(session,page + " is LETTER!")
                os.system(tiff2pscmd + " -h11 " + page + " | " + lprcmd + " -P myprinter -o media=letter -o fitplot=true")
        writeToLog(session,"PDF creation in progress...")
        error = os.system(tiff2pdfcmd + " " + incomingfaxes + "rxfax-" + the_uuid + ".tiff -o " + incomingfaxes + "rxfax-" + the_uuid + ".pdf")
        if error == 0:
            # Generating JPG preview
            writeToLog(session,"Generating JPG preview file (continue on failure)...")
            os.system(convertcmd + " -scale 500 " + incomingfaxes + "rxfax-" + the_uuid + ".tiff[0] " + incomingfaxes + "rxfax-" + the_uuid + ".jpg")
            writeToLog(session,"Sending PDF to FTP server...")
            # We send the PDF on remote server
            error = os.system(ncftpputcmd + " -m -u " + ftpuser + " -p " + ftppass + " " + ftphost + " / " + incomingfaxes + "rxfax-" + the_uuid + ".pdf ")
            os.system(ncftpputcmd + " -m -u " + ftpuser + " -p " + ftppass + " " + ftphost + " / " + incomingfaxes + "rxfax-" + the_uuid + ".jpg ")
            if error == 0:
                # Everything went fine, party time!
                writeToLog(session, "Everything went fine, cleaning up tmp files...")
                os.system('rm -f ' + incomingfaxes + "rxfax-" + the_uuid + ".pdf " + incomingfaxes + "rxfax-" + the_uuid + ".tiff " + incomingfaxes + "rxfax-" + the_uuid + "_*.tiff " + incomingfaxes + "rxfax-" + the_uuid + ".jpg")
            else:
                # FTP failed, we're fucked!
                writeToLog(session,"FTP upload failed, hanging up")
                session.hangup()
        else:
            # PDF couldn't be created, we're fucked!
            #writeToLog(session,"PDF creation FAILED, hanging up")
            mysub = "Fax en provenance de " + the_caller + " à ÉCHOUÉ"
            mytxt = "Raison: Création du fichier PDF à échoué! Fichier à récupérer: " + incomingfaxes + "rxfax-" + the_uuid + ".tiff"
            writeToLog(session,mytxt)
            sendErrorToEmail(mysub,mytxt)
            session.hangup()
    else:
    # FTP host is not working, we cancel right now!
        mysub = "Fax en provenance de " + the_caller + " à ÉCHOUÉ"
        mytxt = "Raison: FTP sur " + ftphost + " est hors service! Erreur Fatal, impossible de récupérer!"
        writeToLog(session,mytxt)
        sendErrorToMail(mysub,mytxt)
        session.hangup()