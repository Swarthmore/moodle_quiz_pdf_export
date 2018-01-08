import pymysql
import string
import re


from pyPdf import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas  
from reportlab.lib.units import inch 
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate,Spacer

from reportlab.pdfbase import _fontdata_enc_winansi
from reportlab.pdfbase import _fontdata_enc_macroman
from reportlab.pdfbase import _fontdata_enc_standard
from reportlab.pdfbase import _fontdata_enc_symbol
from reportlab.pdfbase import _fontdata_enc_zapfdingbats
from reportlab.pdfbase import _fontdata_enc_pdfdoc
from reportlab.pdfbase import _fontdata_enc_macexpert
from reportlab.pdfbase import _fontdata_widths_courier
from reportlab.pdfbase import _fontdata_widths_courierbold
from reportlab.pdfbase import _fontdata_widths_courieroblique
from reportlab.pdfbase import _fontdata_widths_courierboldoblique
from reportlab.pdfbase import _fontdata_widths_helvetica
from reportlab.pdfbase import _fontdata_widths_helveticabold
from reportlab.pdfbase import _fontdata_widths_helveticaoblique
from reportlab.pdfbase import _fontdata_widths_helveticaboldoblique
from reportlab.pdfbase import _fontdata_widths_timesroman
from reportlab.pdfbase import _fontdata_widths_timesbold
from reportlab.pdfbase import _fontdata_widths_timesitalic
from reportlab.pdfbase import _fontdata_widths_timesbolditalic
from reportlab.pdfbase import _fontdata_widths_symbol
from reportlab.pdfbase import _fontdata_widths_zapfdingbats
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bs4 import BeautifulSoup

REMOVE_ATTRIBUTES = ['font']


# ==================== Fill out this info ====================
moodle_db_host = ""
moodle_db_user = ""
moodle_db_pass = ""
moodle_db_port = 
moodle_db_name = ""

quiz_id = "342"
test_name = "INTRO PEACE AND CONFLICT STUDIES FINAL EXAM FALL 2014"

# =============================================================

pdfmetrics.registerFont(TTFont('trebuchet ms', '/Library/Fonts/Trebuchet MS.ttf'))
pdfmetrics.registerFont(TTFont('trebuchet ms-Bold', '/Library/Fonts/Trebuchet MS Bold.ttf'))
pdfmetrics.registerFont(TTFont('trebuchet ms-Italic', '/Library/Fonts/Trebuchet MS Italic.ttf'))
pdfmetrics.registerFont(TTFont('trebuchet ms-BoldItalic', '/Library/Fonts/Trebuchet MS Bold Italic.ttf'))

conn = pymysql.connect (host = moodle_db_host,
						port = moodle_db_port,
                           user = moodle_db_user,
                           db = moodle_db_name,
                           passwd= moodle_db_pass
                           )
print "Connected to Moodle"                           
                           
                           
cur = conn.cursor()

cur.execute("select name, questions from mdl_quiz where id=" + quiz_id)

r = cur.fetchone()
print r[1]
questions = string.split(r[1],",")

# Get the question title and name
question_list = []

for q in questions:
	if q!="0":
		print "Getting info for question #" + q
		cur.execute("select name, questiontext from mdl_question where id=" + q)
		r = cur.fetchone()
		question_list.append({"id":q, "title":r[0], "text":r[1]})

print question_list		

# Get list of students and the corresponding attempt number
# Note - this would need to be refine if there can be more than one attempt
cur.execute("select mdl_quiz_attempts.uniqueid as attemptID, concat(mdl_user.firstname, ' ', mdl_user.lastname) as name, mdl_user.id from mdl_quiz_attempts, mdl_user where mdl_quiz_attempts.userid = mdl_user.id and state='finished' and quiz=" + quiz_id)

student_responses=dict()
for attempts in cur.fetchall():

	# Create dict entry for this student
	student_responses[attempts[2]] = {'name':attempts[1], 'answers':[]}
	print "Now getting responses for " + attempts[1]
	

	for question in question_list:
	
		if question["id"] != 0:
			cur2 = conn.cursor()
			cur2.execute("select * from (select question, answer, timestamp, attempt from mdl_question_states where attempt = " + str(attempts[0]) + " and question=" + question["id"] + " order by mdl_question_states.seq_number DESC) as tmp_table group by attempt")
			
			cur2.execute("SELECT quiza.userid,quiza.quiz,quiza.id AS quizattemptid,quiza.attempt, qu.preferredbehaviour,qa.slot,qa.questionid,qa.maxmark, qa.minfraction,qas.sequencenumber, qas.state, FROM_UNIXTIME(qas.timecreated), qas.userid, qa.questionsummary,qa.responsesummary FROM mdl_quiz_attempts quiza JOIN mdl_question_usages qu ON qu.id = quiza.uniqueid JOIN mdl_question_attempts qa ON qa.questionusageid = qu.id JOIN mdl_question_attempt_steps qas ON qas.questionattemptid = qa.id LEFT JOIN mdl_question_attempt_step_data qasd ON qasd.attemptstepid = qas.id WHERE quiza.uniqueid = " + str(attempts[0]) + " and qas.state='needsgrading' and qa.questionid = %s ORDER BY quiza.userid, quiza.attempt, qa.slot, qas.sequencenumber, qasd.name;" % (question["id"]))
			
			ans = cur2.fetchone()
			answer = "Not answered"
			if ans is not None:
				answer = ans[14]
			student_responses[attempts[2]]["answers"].append(answer)

print "Now formatting output"

for student in student_responses.keys():
	print student_responses[student]["name"]
	test_file_name = test_name + "_" + student_responses[student]["name"] + ".pdf"
	pdf = SimpleDocTemplate(test_file_name, pagesize = letter, rightMargin=72,leftMargin=72, topMargin=36,bottomMargin=18)
	
	# Create the content 
	story = []
	style = getSampleStyleSheet()
	story.append(Paragraph(student_responses[student]["name"], style["Heading1"]))
	story.append(Paragraph("<br/>", style["Normal"]))
	
	q = 0
	for question in question_list: 
		#print question["text"]
		# remove all attributes in REMOVE_ATTRIBUTES from content, 
		# but preserve the tag and its content. 
		
		# Needed to use unicode for some unusual characters.
		#resp = unicode(student_responses[student]["answers"][q], "ISO-8859-1") 
		resp = student_responses[student]["answers"][q]
		resp = resp.replace("\r\n", "<br />")
		resp = resp.replace("\n", "<br />")
		
		soup = BeautifulSoup(resp)
		
		for tag in REMOVE_ATTRIBUTES: 
			for match in soup.findAll(tag):
				match.replaceWithChildren()

		for match in soup.findAll('span'):
			match.unwrap()

		resp = soup.prettify()
		
		# Replace carriage returns with line breaks
		string.replace(resp, "\r", "<br/>")
		print resp
		
		# Question number (uncomment if not printing the question (see below)
		#story.append(Paragraph("#" + str(q+1), style["Heading3"]))
		
		# Uncomment if the text of the question should appear -- this needs work!
		# Sometimes the unicode conversion is necessary for certain characters, but it messes up quotes
		story.append(Paragraph("#" + str(q+1) + ")  " + unicode(question["text"], "ISO-8859-1"), style["Heading3"]))		
		story.append(Paragraph(resp, style["Normal"]))
		q = q+1
				
	pdf.build(story)


cur.close()
conn.close()



