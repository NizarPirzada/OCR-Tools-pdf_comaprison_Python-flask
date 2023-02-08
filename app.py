from flask import Flask,request,jsonify,render_template,send_file,Response
import base64
from flask_bootstrap import Bootstrap
import sqlite3
import re
from difflib import SequenceMatcher
from flask_cors import CORS
import PyPDF2
import difflib
import fitz
from zipfile import ZipFile
import uuid
import sys
import os
from pathlib import Path
import logging
from flask_migrate import Migrate
from config import Config
from flask_sqlalchemy import SQLAlchemy

ALLOWED_EXTENSIONS = {'pdf'}
app = Flask(__name__)

app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import ReferenceFile, OriginalFile, ReferenceFileRegex

CORS(app)
Bootstrap(app)
app.secret_key = '12345'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_reference', methods=['GET', 'POST'])
def upload_reference_file():
    uu_id = uuid.uuid1()
    #### POST REQUEST FOR UPLOAD, DELETE
    if request.method == 'POST':
        #### UPLOAD
        if request.files:
            desc = request.form['description']
            file_ref = request.files['reference']

            count = 1
            regex_list = []
            while True:
                try:
                    reg = request.form['regex' + str(count)]
                    if reg == '':
                        break 
                    else:
                        regex_list.append(reg)
                except Exception:
                    break
                count += 1 
            
            files_json = [{'file_ref':file_ref.filename,'uuid':str(uu_id.int), 'desc':desc}]
            try:
                if  allowed_file(file_ref.filename):
                    blob_ref = base64.b64encode(file_ref.read())
                    ref = ReferenceFile(
                        uuid=str(uu_id.int), 
                        reference_pdf_name=file_ref.filename,
                        reference_pdf=blob_ref,
                        description=desc)
                    db.session.add(ref)
                    db.session.commit()

                    for i, reg in enumerate(regex_list):
                        ref_regex = ReferenceFileRegex(
                            regex=reg,
                            uuid_ref=str(uu_id.int))
                        db.session.add(ref_regex)
                    db.session.commit()

                    return jsonify(files_json)
                else:
                    return Response("All fields must be selected", status=400, mimetype='application/json')
            except Exception:
                # exc_type, exc_obj, exc_tb = sys.exc_info()
                # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                # print(exc_type, fname, exc_tb.tb_lineno)
                logging.error("Exception occurred", exc_info=True)
                return Response("Error in uploading", status=400, mimetype='application/json')
        #### DELETE
        else:
            uuid_value = request.json['uuid']

            ReferenceFileRegex.query.filter_by(uuid_ref = uuid_value).delete()
            db.session.commit()

            ref = ReferenceFile.query.filter_by(uuid = uuid_value).one()
            db.session.delete(ref)
            db.session.commit()
            return jsonify('')
    #### GET REQUEST FOR GET RESULTS
    else:
        try:
            refs = ReferenceFile.query.all()
            db_data = []
            for ref in refs:
                db_data.append((ref.uuid, ref.reference_pdf_name, ref.description))
            
            return jsonify(db_data)
        except Exception:
            return jsonify('')

@app.route('/update_reference', methods=['GET', 'POST'])
def update_reference_file():
    #### POST REQUEST FOR UPDATE
    if request.method == 'POST':
        if request.files:
            try:
                uuid = request.form['uuid']
                desc = request.form['desc']
                file_ref = request.files['reference']
                files_json = [{'file_ref':file_ref.filename,'uuid':str(uuid),'desc':desc}]
                try:
                    if allowed_file(file_ref.filename):
                        blob_ref = base64.b64encode(file_ref.read())
                        
                        ref = ReferenceFile.query.filter_by(uuid = uuid).one()
                        ref.reference_pdf_name = file_ref.filename
                        ref.reference_pdf = blob_ref
                        ref.description = desc
                        db.session.commit()
                        
                        return jsonify(files_json)
                    else:
                        return Response("All fields must be selected - inner", status=400, mimetype='application/json')
                except Exception:
                    # exc_type, exc_obj, exc_tb = sys.exc_info()
                    # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    # print(exc_type, fname, exc_tb.tb_lineno)
                    logging.error("Exception occurred", exc_info=True)
                    return Response("Error in uploading", status=400, mimetype='application/json')
            except Exception:
                return Response("All fields must be selected - outer", status=400, mimetype='application/json')
    else:
        return Response("Bad request", status=400, mimetype='application/json')    


@app.route('/upload_original', methods=['GET', 'POST'])
def upload_original_file():
    uu_id = uuid.uuid1()
    if request.method == 'POST':
        if request.files:
            resp_String = request.__str__
            try:
                desc = request.form['description']
                resp_String += " found descrption"
                ref_uuid = request.form['reference_uuid']
                resp_String += " found reference_uuid"
                file_orig = request.files['original']
                resp_String += " found file original"
                files_json = [{'file_orig':file_orig.filename,'uuid':str(uu_id.int), 'desc':desc, 'ref_uuid':ref_uuid}]
                if allowed_file(file_orig.filename):
                    blob_orig = base64.b64encode(file_orig.read())
                    orig = OriginalFile(
                        uuid=str(uu_id.int), 
                        original_pdf_name=file_orig.filename,
                        original_pdf=blob_orig,
                        description=desc,
                        uuid_ref=ref_uuid)
                    db.session.add(orig)
                    db.session.commit()
                    
                    return jsonify(files_json)
                else:
                    return Response("All fields must be selected - inner", status=422, mimetype='application/json')
            except Exception as e:
                # exc_type, exc_obj, exc_tb = sys.exc_info()
                # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                # print(exc_type, fname, exc_tb.tb_lineno)
                logging.error("Exception occurred", exc_info=True)
                return Response(f"All fields must be selected - outer {resp_String}, Exception {e}", status=422, mimetype='application/json')
        else:
            uuid_value = request.json['uuid']
            try:
                orig = OriginalFile.query.filter_by(uuid = uuid_value).one()
                db.session.delete(orig)
                db.session.commit()
            except Exception:
                pass
            return jsonify('')
    else:
        try:
            origs = OriginalFile.query.all()
            db_data = []
            for orig in origs:
                db_data.append((orig.uuid, orig.original_pdf_name, orig.description, orig.uuid_ref))
            
            return jsonify(db_data)
        except Exception:
            return jsonify('')
    

@app.route('/comparison',methods=['POST', 'GET'])
def comparison_():
    if request.method == 'GET':
        try:
            basedir = Path.cwd()
            uuid1 = request.args.get('uuid1', None)
            uuid2 = request.args.get('uuid2', None)
            
            orig = OriginalFile.query.filter_by(uuid = uuid1).one()
            blob = orig.original_pdf
            blob_orig = base64.b64decode(blob)

            with open(basedir.joinpath('temp', 'temp_orig.pdf'), 'wb') as f:
                f.write(blob_orig)

            ref = ReferenceFile.query.filter_by(uuid = uuid2).one()
            blob = ref.reference_pdf
            blob_ref = base64.b64decode(blob)

            with open(basedir.joinpath('temp', 'temp_ref.pdf'), 'wb') as f:
                f.write(blob_ref)


            input_file1 = Path() / 'temp' / 'temp_orig.pdf'
            input_file2 = Path() / 'temp' / 'temp_ref.pdf'

            output_file1 = Path() / 'output' / 'Original_file.pdf'
            output_file2 = Path() / 'output' / 'Reference_file.pdf'

            msg = 'Comparing files ' + str(input_file1) + ' and ' + str(input_file2) + '.....'
            logging.info(msg)

            pdf_file_obj = open(input_file1, 'rb')

            #The pdfReader variable is a readable object that will be parsed
            pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)

            #discerning the number of pages will allow us to parse through all #the pages
            num_pages = pdf_reader.numPages
            count = 0
            text = ""
            pages1 = []

            #The while loop will read each page
            while count < num_pages:
                page_obj = pdf_reader.getPage(count)
                count +=1
                temp = page_obj.extractText()
                text += temp
                pages1.append(temp)

            full_text1 = text
            full_text1 = full_text1.replace('\n', ' ')
            full_text1 = full_text1.replace(' \n', ' ')
            full_text1 = re.sub(' +', ' ', full_text1)

            while True:
                try:
                    inz = full_text1.index('Seite')
                    temp = ' '.join(full_text1[inz:].split()[:4])
                    full_text1 = full_text1.replace(temp, '')
                except Exception:
                    break
            pdf_file_obj.close()

            pdf_file_obj = open(input_file2, 'rb')

            #The pdfReader variable is a readable object that will be parsed
            pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)

            #discerning the number of pages will allow us to parse through all #the pages
            num_pages = pdf_reader.numPages
            count = 0
            text = ""
            pages2 = []

            #The while loop will read each page
            while count < num_pages:
                page_obj = pdf_reader.getPage(count)
                count +=1
                temp = page_obj.extractText()
                text += temp
                pages2.append(temp)


            full_text2 = text
            full_text2 = full_text2.replace('\n', ' ')
            full_text2 = full_text2.replace(' \n', ' ')
            full_text2 = re.sub(' +', ' ', full_text2)

            while True:
                try:
                    inz = full_text2.index('Seite')
                    temp = ' '.join(full_text2[inz:].split()[:4])
                    full_text2 = full_text2.replace(temp, '')
                except Exception:
                    break

            pdf_file_obj.close()

            str1 = full_text1
            str2 = full_text2

            delta = difflib.Differ().compare(str1.split(), str2.split())
            # difflist = []
            one = []
            two = []


            for line in delta:
                if line[0] == '?':
                    continue
                elif line[0] == ' ':
                    continue
                else:
                    if line[0] == '-':
                        one.append(line[2:])
                    elif line[0] == '+':
                        two.append(line[2:])

                    # difflist.append(line)


            # mix = [l[:] for l in '\n'.join(difflist).splitlines() if l]
            one = [l[:] for l in '\n'.join(one).splitlines() if l]
            two = [l[:] for l in '\n'.join(two).splitlines() if l]

            one_text = ' '.join(one)
            two_text = ' '.join(two)

            one_final = one_text
            two_final = two_text
            matches = SequenceMatcher(None, one_text, two_text).get_matching_blocks()
            for match in matches:
                sen = one_text[match.a:match.a + match.size]
                if len(sen) > 6:
                    
                    one_final = one_final.replace(sen, ' ', 1)
                    two_final = two_final.replace(sen, ' ', 1)

            one_text = one_final
            two_text = two_final

            matches = SequenceMatcher(None, two_text, one_text).get_matching_blocks()
            for match in matches:
                sen = two_text[match.a:match.a + match.size]
                if len(sen) > 6:
                    
                    one_final = one_final.replace(sen, ' ', 1)
                    two_final = two_final.replace(sen, ' ', 1)

            
            msg = 'Generating ' + str(output_file1) + '.....'
            logging.info(msg)


            one_list = one_final.split()

            doc1 = fitz.open(input_file1)
            page_no = 0
            for word in one_list:
                for i in range(page_no, len(pages1)):
                    if word in pages1[i]:
                        page = doc1[i]
                        text_instances = page.searchFor(word)
                        for inst in text_instances:
                            highlight = page.addHighlightAnnot(inst)
                            break
                        break
                    page_no += 1
            try:
                if one_list[0].isdigit():
                    word = one_list[0]
                    for i in range(len(pages1)):
                        page = doc1[i]
                        text_instances = page.searchFor(word)
                        for inst in text_instances:
                            highlight = page.addHighlightAnnot(inst)
                            break
            except Exception:
                pass
            doc1.save(output_file1, garbage=4, deflate=True, clean=True)

            
            msg = 'Generating ' + str(output_file2) + '.....'
            logging.info(msg)
            two_list = two_final.split()

            # for i, page in enumerate(pages1):
            doc2 = fitz.open(input_file2)
            page_no = 0
            for word in two_list:
                for i in range(page_no, len(pages2)):
                    if word in pages2[i]:
                        page = doc2[i]
                        text_instances = page.searchFor(word)
                        for inst in text_instances:
                            highlight = page.addHighlightAnnot(inst)
                            break
                        break
                    page_no += 1
            try:
                if two_list[0].isdigit():
                    word = two_list[0]
                    for i in range(len(pages2)):
                        page = doc2[i]
                        text_instances = page.searchFor(word)
                        for inst in text_instances:
                            highlight = page.addHighlightAnnot(inst)
                            break
            except Exception:
                pass
            doc2.save(output_file2, garbage=4, deflate=True, clean=True)
            zip_obj = ZipFile(basedir.joinpath('output', 'output.zip'), 'w')
            zip_obj.write(output_file1)
            zip_obj.write(output_file2)
            zip_obj.close()

            msg = 'Finish'
            logging.info(msg)
        except Exception:
            logging.error("Exception occurred", exc_info=True)
            return Response("Error in Comparison", status=400, mimetype='application/json')

        if one_final == "" and two_final == "":
            resp = {'result' : 'OK'}
            return jsonify(resp)

        else:
            resp = {'result' : {'orig_file_diff' : one_final, 'ref_file_diff': two_final}}
            return jsonify(resp)

        
    else:
        return Response("Bad Request", status=400, mimetype='application/json')

@app.route('/download_comparison',methods=['POST', 'GET'])
def download_comparison_():
    if request.method == 'GET':
        basedir = Path.cwd()
        return send_file(basedir.joinpath('output', 'output.zip'), as_attachment=True)
        
@app.route('/')
def index():
    return render_template('default.html')

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    app.run(host='0.0.0.0')