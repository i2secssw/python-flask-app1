#' _*_ coding: utf-8 _*_
from flask import Flask, render_template, redirect, send_from_directory, request, make_response, session, escape, render_template_string, send_file, send_from_directory, jsonify, url_for
import sys, unicodedata, os, time, datetime, mysql.connector, hashlib, shutil
from mysql.connector.errors import Error
from werkzeug import secure_filename

app = Flask(__name__)
app.secret_key = 'a'
app.config['UPLOAD_FOLDER'] = "/home/i2sec/flask_app/webhacking/uploads"

host ='localhost'
data_base = 'webhacking'
user ='root'
password = '1234'


@app.route('/')
def index(): 
    if request.cookies.get('Level') != '0' and request.cookies.get('Id') != "" and request.cookies.get('Level') != None and request.cookies.get('Id') != None:
        return redirect('/main')
    else:
        resp = make_response(render_template('index.html'))
        resp.set_cookie('Id', "")
        resp.set_cookie('Level', '0')
        return resp


@app.route('/main')
def main():
    if 'userId' in session:
        return redirect('/main/list')
        
    if  request.cookies.get('Id') == None:
        return redirect('/') 
    session['userId'] = request.cookies.get('Id')
    return "<script>alert('%s님 환영합니다.'); window.location='/main/list';</script>" % str(session['userId'])


@app.route('/main/list',methods=['GET','POST'])
#기본적으로 get방식이고, search일 때는 post 방식 post일 때를 위로 해서 search(제목) 할 때 그에 해당하는 게시글만 select해서 출력하게
#취약한 쿼리문은 select * board where bbs_title='' order by bbs_no desc

def main_list():
    if request.cookies.get('Level') == '2' and request.cookies.get('Id') != 'admin':
        Id = 'admin' 
	session['userId'] = Id
	resp = make_response(redirect('/main'))
	resp.set_cookie('Id',Id)
	return resp

    if request.method == 'POST':
	keyword = request.form['keyword']
	column = request.form['column']
	try:
            conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base)
	    cursor = conn.cursor()

     	    if str(column) == 'bbs_title':            
 	 	sql_str = "select * from board where bbs_title = '%s' order by bbs_no desc" % (keyword)
	
	    if str(column) == 'bbs_content':        
		sql_str = "select * from board where bbs_content = '%s' order by bbs_no desc" % (keyword)
 
            cursor.execute(sql_str)
	    result = [] 
	    rows = cursor.fetchall()

	    if rows:
	        result = list(rows)
	        for i in range(0,len(result)):
	            if type(i) != int:
                        result[i] = ''.join(result[i])
	                result[i] = unicodedata.normalize('NFKD',result[i]).encode('ascii','ignore')
	    return render_template('/board/list.html', userId=session['userId'], list=result, searchkeyword=keyword)
	except mysql.connector.Error as err:
            return err.msg
    

    if request.method == 'GET':
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base)
        cursor = conn.cursor()      
        sql_str = "select * from board order by bbs_no desc"
        cursor.execute(sql_str)
        result = [] 
        rows = cursor.fetchall()

        if rows:
            result = list(rows)
            for i in range(0,len(result)):
                if type(i) != int:
                    result[i] = ''.join(result[i])
                    result[i] = unicodedata.normalize('NFKD',result[i]).encode('ascii','ignore')

        return render_template('/board/list.html', userId=session['userId'], list=result)


@app.route('/main/view',methods=['GET'])
def main_view():
    if request.method == 'GET':
        bbs_no = request.args.get('bbs_no')
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base)
        cursor = conn.cursor()      
        #sql_str = "select * from board where bbs_no = '%s'" % bbs_no
        sql_str = "select * from board where bbs_no = %s" % bbs_no
        cursor.execute(sql_str)
        result = []
        rows = cursor.fetchone()
        try:
            fileExist = rows[8]
        except TypeError:
            fileExist = ''
        if rows:
            sql_str = "update board set bbs_count = bbs_count+1 where bbs_no=%s" % (bbs_no)
            cursor.execute(sql_str)
            conn.commit()
            result = list(rows)
            return """
		<html>
    <head>
    <title>게시판</title>
        <div id="logo">
	  <a href='/'>
            <img src="http://www.gdians.com/img/logo.png" style="width:140px;" alt="i2sec_logo">
          </a>
        </div>
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.0/css/bootstrap.min.css">
            <style>
              #bbs_content {
                vertical-align:middle;
              }
              #logo {
              margin-left:15px; 
              margin-top: 15px; 
              }
            </style>
            </head> 
            <div class="container" align='center'>
                    <h1 style="margin-bottom:20px;">게시글 내용</h1>
                <form name="bbs_view" method="" action="" onsubmit="" >
                <div class="table-responsive-md">
                    <table  align='center' border='1' class="table"> 
                        <tr>
                            <td>작성자</td>
                            <td>%s</td>
                        </tr>
                        <tr>
                            <td>제 목</td> 
                            <td>%s</td>
                        </tr>
                        <tr>
                            <td>파 일</td>
                            <td><a href='/filedownload?file=%s'>%s</a></td>
                            <!--<td><textarea name='bbs_content' rows ="20" cols="120" readonly>/textarea></td>-->
                        </tr>
                        <tr>
                            <td id="bbs_content" style="width: 68px;">내 용</td>
                            <td style="height:400px" valign=top>%s</td>
                            <!--<td><textarea name='bbs_content' rows ="20" cols="120" readonly></textarea></td>-->
                        </tr>
                        <tr>
                            <td colspan="2">
                            <div align="center">
                            <input type="button" class="btn btn-primary" value="목록" onclick="location.href='/'">
                            <input type="button" class="btn btn-primary" value="수정" onclick="location.href='/main/revision?bbs_no=%s'">
                            <input type="button" class="btn btn-primary" value="삭제" onclick="location.href='/main/delete?bbs_no=%s'">
                            </div>
                            </td>
                        </tr> 
                    </table>
                </div>
                </form> 
            </div>
            </html>
        """ % (result[3].encode('utf-8'), result[1].encode('utf-8'), fileExist.encode('utf-8'), fileExist.encode('utf-8'), result[2].encode('utf-8'), str(result[0]).encode('utf-8'), str(result[0]).encode('utf-8'))

        else:
            return """
            <head>
              <title>게시판</title>
              <div id="logo">
                <a href="/">
                  <img src="http://www.gdians.com/img/logo.png" style="width: 140px;" alt="i2sec_logo">
                </a>
              </div>
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.0/css/bootstrap.min.css">
            <style>
            #bbs_content{
            vertical-align: middle;
            }
            #logo {
            margin-left:15px;
            margin-top:15px;
            }
            </style>
            </head>
            <div class="container" align='center'>
                    <h1 style="margin-bottom:20px;">게시글 내용</h1>
                <form name="bbs_view" method="" action="" onsubmit="" >
                <div class="table-responsive-md">
                    <table  align='center' border='1' class="table">
                        <tr>
                            <td>작성자</td>
                            <td>%s</td>
                        </tr>
                        <tr>
                            <td>제 목</td>
                            <td>%s</td>
                            <!--<td><textarea name='bbs_content' rows ="20" cols="120" readonly>/textarea></td>-->
                        </tr>
                        <tr>
                            <td>파 일</td> 
                            <td><a href='/filedownload?file=%s'>%s</a></td>
                        </tr>
                        <tr>
                            <td id="bbs_content" style="width: 68px;">내 용</td>
                            <td style="height:400px" valign=top>%s</td>
                            <!--<td><textarea name='bbs_content' rows ="20" cols="120" readonly></textarea></td>-->
                        </tr>
                        <tr>
                            <td colspan="2">
                            <div align="center">
                            <input type="button" class="btn btn-primary" value="목록" onclick="location.href='/'">
                            </div>
                            </td>
                        </tr>
                    </table>
                  </div>
                </form>
            </div>
            </html>
        """ % (result[3].encode('utf-8'), result[1].encode('utf-8'), fileExist.encode('utf-8'), fileExist.encode('utf-8'), result[2].encode('utf-8'))

@app.route('/dupchk')
def dupchk():
    input_data = request.args.get('user_id')
    if input_data != '':
        conn = conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base, use_unicode=True, charset="utf8")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM member where user_id='%s'" % (input_data))
        rv = cursor.fetchone()
        cursor.close()
        conn.close()
        if rv:
            return jsonify({'check':False})
        else:
            return jsonify({'check':True})
    else:
        return "<script>alert('아이디를 입력하세요'); history.back();</script>"

@app.route('/hi/')
def hi():
    if request.args.get('name'):
        name = request.args.get('name')
        template = '''<h2>Hello %s</h2>''' % name
    return render_template_string(template)


@app.route('/main/write')
def main_write():
    if 'userId' in session:
        return render_template('/board/write.html')
    else:
        return "<script>alert('잘못된 접근입니다.'); window.location='/';</script>"

@app.route('/write_chk',methods=['POST'])
def write_chk():
    now = time.localtime()
    bbs_title   = request.form['bbs_title']
    bbs_content = request.form['bbs_content']
    bbs_writer  = request.form['bbs_writer']
    bbs_date = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    bbs_count = 0
    secret_status = 'n'
    bbs_pass = request.form['bbs_pass']

    if bbs_pass != "":
        secret_status = 'y'

    conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base, use_unicode=True, charset="utf8")
    cursor = conn.cursor()
    cursor.execute('SELECT bbs_no FROM board ORDER BY bbs_no DESC LIMIT 1')
    try:
        max_id = cursor.fetchone()[0]    
    except TypeError:
        max_id = 1
    cursor.execute('ALTER TABLE board AUTO_INCREMENT=%s' % str(max_id))    
    conn.commit()
    try:
        f = request.files['_file']
        data = (bbs_title, bbs_content, bbs_writer, bbs_date, bbs_count, secret_status, bbs_pass, f.filename)
        if max_id == 1:
            os.mkdir(app.config['UPLOAD_FOLDER']+ "/" + str(max_id))
            f.save(app.config['UPLOAD_FOLDER'] + str(max_id) + '/' + secure_filename(f.filename))
        else:
            os.mkdir(app.config['UPLOAD_FOLDER']+ "/" + str(max_id+1))
            f.save(app.config['UPLOAD_FOLDER'] + str(max_id+1) + '/' + secure_filename(f.filename))
        sql_str = "insert into board values('', %s, %s, %s, %s, %s, %s, %s, %s)"    
    except KeyError:
        data = (bbs_title, bbs_content, bbs_writer, bbs_date, bbs_count, secret_status, bbs_pass)
        sql_str = "insert into board values('', %s, %s, %s, %s, %s, %s, %s, '')"
    
    cursor.execute(sql_str,data)
    conn.commit()
    cursor.execute('SELECT * FROM board')
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if len(res) == 1:
        return "<script>alert('작성한 게시글이 등록되었습니다.'); window.location='/main/view?bbs_no=1';</script>"
    else:
        return "<script>alert('작성한 게시글이 등록되었습니다.'); window.location='/main/view?bbs_no=%s';</script>" %(str(max_id+1))

@app.route('/main/revision')
def main_revision():
    if 'userId' in session:
        bbs_no = request.args.get('bbs_no')
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base, use_unicode=True, charset="utf8")
        cursor = conn.cursor()
        sql_str = "SELECT * FROM board WHERE bbs_no=%s" % (str(bbs_no))
        cursor.execute(sql_str)
        res = cursor.fetchone()
        cursor.close()
        conn.close()
        if res[3] == session['userId']:
            return render_template('/board/revision.html', bbs_no=bbs_no, res=res)
        else:
            return "<script>alert('잘못된 접근입니다.'); window.location='/';</script>"
    else:
        return "<script>alert('잘못된 접근입니다.'); window.location='/';</script>"

@app.route('/revision_chk', methods=["POST"])
def revision_chk():
    bbs_no = request.args.get('bbs_no')
    conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base, use_unicode=True, charset="utf8")
    cursor = conn.cursor()
    sql_str = "SELECT * FROM board WHERE bbs_no=%s" % (str(bbs_no))
    cursor.execute(sql_str)
    res = cursor.fetchone()
        
    if res[7] == request.form['bbs_pass']:
        bbs_title = request.form['bbs_title'] if len(request.form['bbs_title']) > 1 else res[1]
        bbs_content = request.form['bbs_content'] if len(request.form['bbs_content']) > 1 else res[2]
        bbs_date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

        try:
            f = request.files['_file']
            if res[8] != '':
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'],str(bbs_no) + '/' + res[8]))
            else:
                os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'], str(bbs_no)))
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],str(bbs_no) + '/' + secure_filename(f.filename)))
            data = (bbs_title, bbs_content, bbs_date, f.filename, str(bbs_no))
            sql_str = "UPDATE board SET bbs_title=%s, bbs_content=%s, bbs_date=%s, bbs_file=%s WHERE bbs_no=%s"
        except KeyError:
           data = (bbs_title, bbs_content, bbs_date, str(bbs_no))
           sql_str = "UPDATE board SET bbs_title=%s, bbs_content=%s, bbs_date=%s WHERE bbs_no=%s"
        cursor.execute(sql_str, data)
        conn.commit()
        cursor.close()
        conn.close()
        return "<script>alert('게시글이 수정되었습니다.'); window.location='/';</script>"
    else:
        return "<script>alert('비밀번호가 올바르지 않습니다.'); history.go(-1);</script>"


@app.route('/main/delete')
def main_delete():
    bbs_no = request.args.get('bbs_no')
    if 'userId' in session:
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base, use_unicode=True, charset="utf8")
        cursor = conn.cursor()
        sql_str = "SELECT * FROM board WHERE bbs_no=%s" % (str(bbs_no))
        cursor.execute(sql_str)
        res = cursor.fetchone()
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], str(bbs_no))):
            shutil.rmtree(os.path.join(app.config['UPLOAD_FOLDER'], str(bbs_no)), ignore_errors=True)
        cursor.close()
        conn.close()
        if res[3] == session['userId']:
            if res[7]:
                return "<script> var pw = prompt('비밀번호를 입력하세요.'); if (pw == %s) { location.href='/delete_chk?bbs_no=%s'; } else { alert('비밀번호가 맞지 않습니다. 다시 시도하세요.');location.href='/main/view?bbs_no=%s'; } </script>" % (res[7].encode('utf-8'), str(bbs_no).encode('utf-8'), str(bbs_no).encode('utf-8'))
            else:
                return "<script> var check = confirm('삭제하시겠습니까?'); if (check == true) { location.href='/delete_chk?bbs_no=%s'; } else { location.href='/main/view?bbs_no=%s'; } </script>" % (str(bbs_no), str(bbs_no))
        else:
            return "<script>alert('잘못된 접근입니다.'); window.location='/';</script>"
    else:
        return "<script>alert('잘못된 접근입니다.'); window.location='/';</script>"

@app.route('/delete_chk')
def delete_chk():
    if 'userId' in session:
        bbs_no = request.args.get('bbs_no')
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base, use_unicode=True, charset="utf8")
        cursor = conn.cursor()
        sql_str = "SELECT * FROM board WHERE bbs_no=%s" % (str(bbs_no))
        cursor.execute(sql_str)
        res = cursor.fetchone()        
        if res[3] == session['userId']:
            cursor.execute('DELETE FROM board WHERE bbs_no=%s' % (str(bbs_no)))
            conn.commit()
        else:
            return "<script>alert('잘못된 접근입니다.'); window.location='/';</script>"
        cursor.close()
        conn.close()
        return "<script>alert('게시글이 삭제되었습니다.'); window.location='/';</script>"
    else:
        return "<script>alert('잘못된 접근입니다.'); window.location='/';</script>"

@app.route('/admin', methods=['GET'])
def admin():
    if request.args.get('name'):
        admin_md5 = hashlib.md5('admin').hexdigest()
        if admin_md5 == request.args.get('name'):
            return send_from_directory('admin','index.html')
        else:
            return "<script>alert('잘못된 접근입니다.'); window.location='/';</script>"
    else:
        return "<script>alert('잘못된 접근입니다.'); window.location='/';</script>"


@app.route('/filedownload', methods=['GET'])
def download_file():
    filename = request.args.get('file')
    conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base, use_unicode=True, charset="utf8")
    cursor = conn.cursor()
    cursor.execute("SELECT bbs_no FROM board WHERE bbs_file='%s'" % filename)
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    return send_from_directory(directory=os.path.join(app.config['UPLOAD_FOLDER'],str(res[0])), filename=filename, as_attachment=True)    

@app.route('/signup')
def signup():
    return render_template('/user/signup.html')


@app.route('/signup_chk',methods=['POST'])
def signup_chk():
    if request.method == "POST":
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base, use_unicode=True, charset="utf8")
        cursor = conn.cursor()
        user_name = request.form['user_name']
        user_id = request.form['user_id']
        
        sql_str="select user_id from member where user_id='%s'" % (user_id)
        cursor.execute(sql_str)
        rows = cursor.fetchone()
        
        if rows > 0:
            return "<script>alert('이미 사용하고 있는 아이디입니다.'); window.location='/signup';</script>"
        
        user_pass = request.form['user_pass']
        user_registration_number = request.form['user_registration_number']
        user_birth_year = request.form['user_birth_year']
        user_birth_month = request.form['user_birth_month']
        user_birth_day = request.form['user_birth_day']
        user_addr = request.form['user_addr']
        user_mail = request.form['user_mail']
        
        data = (user_name, user_id, user_pass, user_registration_number, user_birth_year, user_birth_month, user_birth_day, user_addr, user_mail)
        sql_str = "insert into member values('', %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql_str,data)
        conn.commit()
        cursor.close()
        conn.close()
        return "<script>alert('회원가입이 정상적으로 이루어졌습니다.'); window.location='/';</script>"


@app.route('/login_chk',methods=['GET','POST'])
def login_chk():
    if request.method == "POST":
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base)
        cursor = conn.cursor()
        user_id = request.form['user_id']
        user_pass = request.form['user_pass']      
        sql_str="select * from member where user_id='%s' and user_pass='%s'" % (user_id, user_pass)
        cursor.execute(sql_str)
        result = [] 
        rows = cursor.fetchall()
        if rows:
            result = list(rows[0])

            for i in range(2,len(result)):
                result[i] = ''.join(result[i])
                result[i] = unicodedata.normalize('NFKD',result[i]).encode('ascii','ignore')

                cursor.close()
                conn.close()
                resp = make_response(redirect('/'))
                resp.set_cookie('Id', result[2])
                if result[2] == 'admin':
                    resp.set_cookie('Level','2')
                else:
                    resp.set_cookie('Level', '1')
                return resp
                             
        else:
            app.logger.info("Not Mached!! ID or PW Check Please !!")
            return "<script>alert('잘못된 로그인입니다. 확인 후 다시 시도해 주십시오.'); window.location='/';</script>"
        
        cursor.close()
        conn.close()


@app.route('/myinfo_revision') #회원정보 수정(비밀번호, 비밀번호 확인, 주소, 이메일 )
def myinfo_revision():
    conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base)
    cursor = conn.cursor()
    sql_str="select * from member where user_id='%s'" % (session['userId'])
    cursor.execute(sql_str)
    rows = cursor.fetchall()
    if rows:
        result = list(rows[0])

        for i in range(2,len(result)): # index 0 number, 1이름(한글), 8주소(한글)
            if i == 8:   
                continue
            result[i] = ''.join(result[i])
            result[i] = unicodedata.normalize('NFKD',result[i]).encode('ascii','ignore')

    user_name = result[1]
    user_id = result[2]
    user_registration_number = result[4]
    user_birth_year = result[5]
    user_birth_month = result[6]
    user_birth_day = result[7]
    user_addr = result[8]
    user_mail = result[9]

    return render_template('/user/myinfo_revision.html', user_id = user_id, user_name = user_name, user_registration_number = user_registration_number, user_birth_year = user_birth_year, user_birth_month = user_birth_month, user_birth_day = user_birth_day, user_addr = user_addr, user_mail = user_mail)


@app.route('/myinfo_revision_chk',methods=['POST'])
def myinfo_revision_chk():
    if request.method == "POST":
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base, use_unicode=True, charset="utf8")
        cursor = conn.cursor()
        user_id = request.form['user_id']
        user_pass = request.form['user_pass']
        user_addr = request.form['user_addr']
        data = (user_pass, user_addr, user_id)
        sql_str = "update member set user_pass=%s, user_addr=%s where user_id=%s"
        cursor.execute(sql_str,data)
        conn.commit()
        cursor.close()
        conn.close()
    
    return "<script>alert('회원정보가 정상적으로 변경되었습니다.'); window.location='/';</script>"


@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('Id', "", expires=0)
    resp.set_cookie('Level',"", expires=0)
    session.pop('userId')
    return resp


#################### jinja2  template-injection
@app.route('/hello-template-injection')
def hello_ssti():
    person = {'name':"world", 'secret':"UGhldmJoZj8gYWl2ZnZoei5wYnovcG5lcnJlZg=="}
    if request.args.get('name'):
        person['name'] = request.args.get('name')
    template = '''<h2>Hello %s!</h2>''' % person['name']
    return render_template_string(template, person=person)

####
# Private function if the user has local files.
###
def get_user_file(f_name):
    with open(f_name) as f:
        return f.readlines()

app.jinja_env.globals['get_user_file'] = get_user_file # Allows for use in Jinja2 templates

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=False)
