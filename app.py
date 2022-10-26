from datetime import datetime

from flask import Flask, render_template, request, redirect, make_response, jsonify
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.krafton09


# GET 메인  페이지
@app.route('/')
def main(filter=None):
    all_posts = list(db.posts.find({}, {'_id': False}).sort('idx', -1))
    return render_template('main.html', all_posts=all_posts)


# GET 글 생성 페이지로


@app.route('/post')
def post_form():
    return render_template('post_form.html', post=None)


# POST 글 생성
@app.route('/post', methods=['POST'])
def create_post():
    post_collection = db.posts

    user_email = request.cookies.get('user_email')
    user_name = request.cookies.get('user_name')

    input_title = request.form['input_title']
    input_dtl = request.form['input_dtl']
    reg_time = datetime.now()

    idx_list = list(db.posts.find({}, {'_id': False}).sort('idx', -1).limit(1))

    if len(idx_list) == 0:
        idx = 1
    else:
        idx = idx_list[0]['idx'] + 1

    doc = {
        'idx': idx,
        'writer_name': user_name,
        'writer_email': user_email,
        'title': input_title,
        'description': input_dtl,
        'participants': 0,
        'reg_time': reg_time.strftime('%m-%d %H:%M'),
        'status': '모집중'
    }
    post_collection.insert_one(doc)
    return redirect('/')


# GET 글 상세보기 페이지로
@app.route('/post/<idx>')
def post_dtl(idx=None):
    post_collection = db.posts
    return render_template('post_dtl.html', post=post_collection.find_one({'idx': int(idx)}))


# 글 수정
@app.route('/edit/<idx>')
def post_edit(idx=None):
    post_collection = db.posts
    return render_template('post_form.html', post=post_collection.find_one({'idx': int(idx)}))


# 글 수정
@app.route('/edit/<idx>', methods=['POST'])
def post_update(idx=None):
    db.posts.update_many({'idx': int(idx)},
                         {'$set': {'title': request.form['edited_title'], 'description': request.form['edited_dtl']}})
    return jsonify({'result': 'success'})


# 글 삭제
@app.route('/delete/<idx>')
def post_delete(idx=None):
    db.posts.delete_one({'idx': int(idx)})
    return redirect('/')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/signup')
def signup_page():
    return render_template('signup.html')


@app.route('/api/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_receive = request.form['email_give']
        pw_receive = request.form['pw_give']
        signin_user = db.users.find_one({'email': email_receive})

        if signin_user:
            if (signin_user['pw'] == pw_receive):
                resp = make_response({'result': 'success'})
                resp.set_cookie('user_email', email_receive)
                resp.set_cookie('user_name', signin_user['name'])
                return resp
            else:
                return jsonify({'result': 'fail'})
        else:
            return jsonify({'result': 'fail'})
    else:
        return jsonify({'result': 'fail'})


@app.route('/mypage')
def mypage_page():
    my_account = request.cookies.get("account")
    print(my_account)
    if my_account is None:
        return redirect('/login')
    else:
        account_email = my_account.split("/")[0]
        account_name = my_account.split("/")[1]

    table_infos = [
        {"idx": 1, "title": "Jinja제목1", "name": "Jinja이름1", "status": "모집중", "post-date": "22-10-14", "join-num": 3},
        {"idx": 2, "title": "Jinja제목2", "name": "Jinja이름2", "post-date": "22-10-11", "join-num": 5}
    ]
    return render_template('mypage.html', account_name=account_name, account_email=account_email,
                           tableInfoList=table_infos)


# API 역할을 하는 부분
@app.route('/api/signUp', methods=['POST'])
def signup_post():
    email_receive = request.form['email_give']
    pw_receive = request.form['pw_give']
    name_receive = request.form['name_give']

    finded_user = db.users.find_one({'email': email_receive}, {'_id': False})
    if finded_user is None:
        user = {'email': email_receive, 'pw': pw_receive, 'name': name_receive}
        db.users.insert_one(user)
        return jsonify({'result': 'success', 'comment': "회원가입이 완료되었습니다."})
    else:
        return jsonify({'result': 'error', 'comment': "이미 존재하는 회원 Email 입니다."})


@app.route('/api/addData', methods=['GET'])
def add_data():
    tempdata = {
        "idx": 1,
        "writer_email": "aaa@naver.com",
        "writer_name": "길동",
        "title": "제목",
        "description": "내용",
        "participants": [("bbb@naver.com", "동길")],
        "reg_time": "22-10-15",
        "status": "모집중"
    }

    # 3. mongoDB에 데이터를 넣기
    db.posts.insert_one(tempdata)

    return jsonify({'result': 'success', 'comment': "data 추가가 완료되었습니다."})


@app.route('/api/closePurchase', methods=['POST'])
def closepurchase_post():
    # my_account = request.form['account_give']
    my_account = request.cookies.get("account")
    idx_receive = int(request.form['idx_give'])

    finded_post = db.posts.find_one({'idx': idx_receive}, {'_id': False})
    if finded_post is None:
        return jsonify({'result': 'error', 'comment': "해당하는 idx post가 없습니다."})

    if my_account is None:
        account_email = "fail.com"
        account_name = "fail"
    else:
        account_email = my_account.split("/")[0]
        account_name = my_account.split("/")[1]

    if finded_post["writer_email"] != account_email or finded_post["writer_name"] != account_name:
        return jsonify({'result': 'error', 'comment': "잘못된 사용자의 요청입니다."})

    # 3. mongoDB에 데이터를 넣기
    db.posts.update_one({'idx': idx_receive}, {'$set': {'status': "마감"}})

    return jsonify({'result': 'success', 'comment': "정상적으로 처리되었습니다."})


@app.route('/api/joinPurchase', methods=['POST'])
def joinpurchase_post():
    # my_account = request.form['account_give']
    my_account = request.cookies.get("account")
    idx_receive = int(request.form['idx_give'])

    if my_account is None:
        return jsonify({'result': 'error', 'comment': "잘못된 사용자의 요청입니다."})

    finded_post = db.posts.find_one({'idx': idx_receive}, {'_id': False})
    if finded_post is None:
        return jsonify({'result': 'error', 'comment': "해당하는 idx post가 없습니다."})

    my_list = finded_post["participants"]

    account_email = my_account.split("/")[0]
    account_name = my_account.split("/")[1]
    account_list = [account_email, account_name]
    my_list.append(account_list)

    # 3. mongoDB에 데이터를 넣기
    db.posts.update_one({'idx': idx_receive}, {'$set': {'participants': my_list}})

    return jsonify({'result': 'success', 'comment': "정상적으로 처리되었습니다."})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
