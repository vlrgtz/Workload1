import os
import io
import sys
from flask import send_file
from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_bcrypt import Bcrypt
from flask_session import Session
from database import Base,Accounts,Customers,Users,CustomerLog,Transactions
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker
import datetime
import xlwt
from fpdf import FPDF
from sqlalchemy import text

application = Flask(__name__)
bcrypt = Bcrypt(application)
application.secret_key = os.urandom(24)

# Set up database
engine = create_engine('sqlite:///database.db',connect_args={'check_same_thread': False},echo=True)
Base.metadata.bind = engine
db = scoped_session(sessionmaker(bind=engine))
    
# MAIN
@application.route('/')
@application.route("/dashboard")
def dashboard():
    return render_template("home.html", home=True)

@application.route("/addcustomer" , methods=["GET", "POST"])
def addcustomer():
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] != "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="executive":
        if request.method == "POST":
            cust_ssn_id = int(request.form.get("cust_ssn_id"))
            name = request.form.get("name")
            address = request.form.get("address")
            age= int(request.form.get("age"))
            state = request.form.get("state")
            city = request.form.get("city")
            sql_query = text("SELECT * from customers WHERE cust_ssn_id = :c")
            result = db.execute(sql_query, {"c": cust_ssn_id}).fetchone()
            if result is None :
                result = db.query(Customers).count()
                if result == 0 :
                    query = Customers(cust_id=110110000,cust_ssn_id=cust_ssn_id,name=name,address=address,age=age,state=state,city=city,status='activate')
                else:
                    query = Customers(cust_ssn_id=cust_ssn_id,name=name,address=address,age=age,state=state,city=city,status='activate')
                # result = db.execute("INSERT INTO customers (cust_ssn_id,name,address,age,state,city) VALUES (:c,:n,:add,:a,:s,:city)", {"c": cust_ssn_id,"n":name,"add":address,"a": age,"s":state,"city":city})
                db.add(query)
                db.commit()
                if query.cust_id is None:
                    flash("Data is not inserted! Check you input.","danger")
                else:
                    temp = CustomerLog(cust_id=query.cust_id,log_message="Customer Created")
                    db.add(temp)
                    db.commit()
                    flash(f"Customer {query.name} is created with customer ID : {query.cust_id}.","success")
                    return redirect(url_for('viewcustomer'))
            flash(f'SSN id : {cust_ssn_id} is already present in database.','warning')
        
    return render_template('addcustomer.html', addcustomer=True)

@application.route("/viewcustomer/<cust_id>")
@application.route("/viewcustomer" , methods=["GET", "POST"])
def viewcustomer(cust_id=None):
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] != "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="executive":
        if request.method == "POST":
            cust_ssn_id = request.form.get("cust_ssn_id")
            cust_id = request.form.get("cust_id")
            sql_query = text("SELECT * from customers WHERE cust_id = :c or cust_ssn_id = :d")
            data = db.execute(sql_query, {"c": cust_id, "d": cust_ssn_id}).fetchone()
            if data is not None:
                return render_template('viewcustomer.html', viewcustomer=True, data=data)
            
            flash("Customer not found! Please,Check you input.", 'danger')
        elif cust_id is not None:
            sql_query = text("SELECT * from customers WHERE cust_id = :c")
            data = db.execute(sql_query, {"c": cust_id}).fetchone()
            if data is not None:
                return render_template('viewcustomer.html', viewcustomer=True, data=data)
            
            flash("Customer not found! Please,Check you input.", 'danger')
    else:
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))

    return render_template('viewcustomer.html', viewcustomer=True)

@application.route('/editcustomer')
@application.route('/editcustomer/<cust_id>', methods=["GET", "POST"])
def editcustomer(cust_id=None):
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] != "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="executive":
        if cust_id is not None:
            if request.method != "POST":
                cust_id = int(cust_id)
                sql_query = text("SELECT * from customers WHERE cust_id = :c")
                data = db.execute(sql_query, {"c": cust_id}).fetchone()
                if data is not None and data.status != 'deactivate':
                    return render_template('editcustomer.html', editcustomer=True, data=data)
                else:
                    flash('Customer is deactivated or not present in database.','warning')
            else:
                cust_id = int(cust_id)
                name = request.form.get("name")
                address = request.form.get("address")
                age= int(request.form.get("age"))
                sql_query = text("SELECT * from customers WHERE cust_id = :c and status = 'activate'")
                result = db.execute(sql_query, {"c": cust_id}).fetchone()
                if result is not None :
                    sql_query = text("UPDATE customers SET name = :n , address = :add , age = :ag WHERE cust_id = :a")
                    result = db.execute(sql_query, {"n": name,"add": address,"ag": age,"a": cust_id})
                    db.commit()
                    temp = CustomerLog(cust_id=cust_id,log_message="Customer Data Updated")
                    db.add(temp)
                    db.commit()
                    flash(f"Customer data are updated successfully.","success")
                else:
                    flash('Invalid customer Id. Please, check customer Id.','warning')

    return redirect(url_for('viewcustomer'))

@application.route('/deletecustomer')
@application.route('/deletecustomer/<cust_id>')
def deletecustomer(cust_id=None):
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] != "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="executive":
        if cust_id is not None:
            cust_id = int(cust_id)
            sql_query = text("SELECT * from customers WHERE cust_id = :a and status = 'activate'")
            result = db.execute(sql_query, {"a": cust_id}).fetchone()
            if result is not None :
                # delete from accounts WHERE acc_id = :a and acc_type=:at", {"a": acc_id,"at":acc_type}
                sql_query = text("UPDATE customers SET status='deactivate' WHERE cust_id = :a")
                query = db.execute(sql_query, {"a": cust_id})
                db.commit()
                temp = CustomerLog(cust_id=cust_id,log_message="Customer Deactivated")
                db.add(temp)
                db.commit()
                flash(f"Customer is deactivated.","success")
                return redirect(url_for('dashboard'))
            else:
                flash(f'Customer with id : {cust_id} is already deactivated or not present in database.','warning')
    return redirect(url_for('viewcustomer'))

@application.route('/activatecustomer')
@application.route('/activatecustomer/<cust_id>')
def activatecustomer(cust_id=None):
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] != "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="executive":
        if cust_id is not None:
            cust_id = int(cust_id)
            sql_query = text("SELECT * from customers WHERE cust_id = :a and status = 'deactivate'")
            result = db.execute(sql_query, {"a": cust_id}).fetchone()
            if result is not None :
                sql_query = text("UPDATE customers SET status='activate' WHERE cust_id = :a")
                query = db.execute(sql_query, {"a": cust_id})
                db.commit()
                temp = CustomerLog(cust_id=cust_id,log_message="Customer Activated")
                db.add(temp)
                db.commit()
                flash(f"Customer is activated.","success")
                return redirect(url_for('dashboard'))
            flash(f'Customer with id : {cust_id} is already activated or not present in database.','warning')
    return redirect(url_for('viewcustomer'))

@application.route('/customerstatus')
def customerstatus():
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] != "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="executive":
        # join query to get one log message per customer id
        sql_query = text("SELECT customers.cust_id as id, customers.cust_ssn_id as ssn_id, customerlog.log_message as message, customerlog.time_stamp as date from (select cust_id,log_message,time_stamp from customerlog group by cust_id ORDER by time_stamp desc) as customerlog JOIN customers ON customers.cust_id = customerlog.cust_id group by customerlog.cust_id order by customerlog.time_stamp desc")
        data = db.execute(sql_query).fetchall()
        if data:
            return render_template('customerstatus.html',customerstatus=True , data=data)
        else:
            flash('No data found.','danger')
    return redirect(url_for('dashboard'))

@application.route("/addaccount" , methods=["GET", "POST"])
def addaccount():
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] != "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="executive":
        if request.method == "POST":
            cust_id = int(request.form.get("cust_id"))
            acc_type = request.form.get("acc_type")
            amount= float(request.form.get("amount"))
            message = "Account successfully created"
            sql_query = text("SELECT * from customers WHERE cust_id = :c")
            result = db.execute(sql_query, {"c": cust_id}).fetchone()
            if result is not None :
                sql_query = text("SELECT * from accounts WHERE cust_id = :c and acc_type = :at")
                result = db.execute(sql_query, {"c": cust_id, "at": acc_type}).fetchone()
                if result is None:
                    result = db.query(Accounts).count()
                    if result == 0 :
                        query = Accounts(acc_id=360110000,acc_type=acc_type,balance=amount,cust_id=cust_id,status='active',message=message,last_update=datetime.datetime.now())
                    else:
                        query = Accounts(acc_type=acc_type,balance=amount,cust_id=cust_id,status='active',message=message,last_update=datetime.datetime.now())
                    db.add(query)
                    db.commit()
                    if query.acc_id is None:
                        flash("Data is not inserted! Check you input.","danger")
                    else:
                        flash(f"{query.acc_type} account is created with customer ID : {query.acc_id}.","success")
                        return redirect(url_for('dashboard'))
                else:
                    flash(f'Customer with id : {cust_id} has already {acc_type} account.','warning')
            else:
                flash(f'Customer with id : {cust_id} is not present in database.','warning')

    return render_template('addaccount.html', addaccount=True)

@application.route("/delaccount" , methods=["GET", "POST"])
def delaccount():
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] != "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="executive":
        if request.method == "POST":
            acc_id = int(request.form.get("acc_id"))
            acc_type = request.form.get("acc_type")
            sql_query = text("SELECT * from accounts WHERE acc_id = :a")
            result = db.execute(sql_query, {"a": acc_id}).fetchone()
            if result is not None :
                # delete from accounts WHERE acc_id = :a and acc_type=:at", {"a": acc_id,"at":acc_type}
                sql_query = text("UPDATE accounts SET status='deactive' WHERE acc_id = :a and acc_type=:at")
                query = db.execute(sql_query, {"a": acc_id,"at":acc_type})
                db.commit()
                flash(f"Customer account is Deactivated Successfully.","success")
                return redirect(url_for('dashboard'))
            flash(f'Account with id : {acc_id} is not present in database.','warning')
    return render_template('delaccount.html', delaccount=True)

@application.route("/viewaccount" , methods=["GET", "POST"])
def viewaccount():
    if 'user' not in session:
        return redirect(url_for('login'))        
    if session['usert']=="executive" or session['usert']=="teller" or session['usert']=="cashier":
        if request.method == "POST":
            acc_id = request.form.get("acc_id")
            cust_id = request.form.get("cust_id")
            sql_query = text("SELECT * from accounts WHERE cust_id = :c or acc_id = :d")
            data = db.execute(sql_query, {"c": cust_id, "d": acc_id}).fetchall()
            if data:
                return render_template('viewaccount.html', viewaccount=True, data=data)
            
            flash("Account not found! Please,Check you input.", 'danger')
    else:
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    return render_template('viewaccount.html', viewaccount=True)


@application.route("/viewaccountstatus" , methods=["GET", "POST"])
def viewaccountstatus():
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] != "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="executive":
        sql_query = text("select * from accounts")
        data = db.execute(sql_query).fetchall()
        if data:
            return render_template('viewaccountstatus.html', viewaccount=True, data=data)
        else:
            flash("Accounts are not found!", 'danger')
    return render_template('viewaccountstatus.html', viewaccount=True)

# Code for deposit amount 
@application.route('/deposit',methods=['GET','POST'])
@application.route('/deposit/<acc_id>',methods=['GET','POST'])
def deposit(acc_id=None):
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] == "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="teller" or session['usert']=="cashier":
        if acc_id is None:
            return redirect(url_for('viewaccount'))
        else:
            if request.method == "POST":
                amount = request.form.get("amount")
                sql_query = text("select * from accounts where acc_id = :a and status='active'")
                data = db.execute(sql_query,{"a":acc_id}).fetchone()
                if data is not None:
                    balance = int(amount) + int(data.balance)
                    sql_query = text("UPDATE accounts SET balance= :b WHERE acc_id = :a")
                    query = db.execute(sql_query, {"b":balance,"a": data.acc_id})
                    db.commit()
                    flash(f"{amount} Amount deposited into account: {data.acc_id} successfully.",'success')
                    temp = Transactions(acc_id=data.acc_id,trans_message="Amount Deposited",amount=amount)
                    db.add(temp)
                    db.commit()
                else:
                    flash(f"Account not found or Deactivated.",'danger')
            else:
                sql_query = text("select * from accounts where acc_id = :a")
                data = db.execute(sql_query,{"a":acc_id}).fetchone()
                if data is not None:
                    return render_template('deposit.html', deposit=True, data=data)
                else:
                    flash(f"Account not found or Deactivated.",'danger')

    return redirect(url_for('dashboard'))

# Code for withdraw amount 
@application.route('/withdraw',methods=['GET','POST'])
@application.route('/withdraw/<acc_id>',methods=['GET','POST'])
def withdraw(acc_id=None):
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] == "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="teller" or session['usert']=="cashier":
        if acc_id is None:
            return redirect(url_for('viewaccount'))
        else:
            if request.method == "POST":
                amount = request.form.get("amount")
                sql_query = text("select * from accounts where acc_id = :a and status='active'")
                data = db.execute(sql_query,{"a":acc_id}).fetchone()
                if data is not None:
                    if int(data.balance)>=int(amount):
                        balance =  int(data.balance)-int(amount)
                        sql_query = text("UPDATE accounts SET balance= :b WHERE acc_id = :a")
                        query = db.execute(sql_query, {"b":balance,"a": data.acc_id})
                        db.commit()
                        flash(f"{amount} Amount withdrawn from account: {data.acc_id} successfully.",'success')
                        temp = Transactions(acc_id=data.acc_id,trans_message="Amount Withdrawn",amount=amount)
                        db.add(temp)
                        db.commit()
                    else:
                        flash(f"Account doesn't have sufficient Balance.",'success')
                        return redirect(url_for('viewaccount'))
                else:
                    flash(f"Account not found or Deactivated.",'danger')
            else:
                sql_query = text("select * from accounts where acc_id = :a")
                data = db.execute(sql_query,{"a":acc_id}).fetchone()
                if data is not None:
                    return render_template('withdraw.html', deposit=True, data=data)
                else:
                    flash(f"Account not found or Deactivated.",'danger')

    return redirect(url_for('dashboard'))

# Code for transfer amount 
@application.route('/transfer',methods=['GET','POST'])
@application.route('/transfer/<cust_id>',methods=['GET','POST'])
def transfer(cust_id=None):
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] == "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="teller" or session['usert']=="cashier":
        if cust_id is None:
            return redirect(url_for('viewaccount'))
        else:
            if request.method == 'POST':
                src_type = request.form.get("src_type")
                trg_type = request.form.get("trg_type")
                amount = int(request.form.get("amount"))
                if src_type != trg_type:
                    sql_query = text("select * from accounts where cust_id = :a and acc_type = :t and status='active'")
                    src_data  = db.execute(sql_query,{"a":cust_id,"t":src_type}).fetchone()
                    sql_query = text("select * from accounts where cust_id = :a and acc_type = :t and status='active'")
                    trg_data  = db.execute(sql_query,{"a":cust_id,"t":trg_type}).fetchone()
                    if src_data is not None and trg_data is not None:
                        if src_data.balance > amount:
                            src_balance = src_data.balance - amount
                            trg_balance = trg_data.balance + amount
                            sql_query = text("update accounts set balance = :b where cust_id = :a and acc_type = :t")
                            test = db.execute(sql_query,{"b":src_balance,"a":cust_id,"t":src_type})
                            db.commit()
                            temp = Transactions(acc_id=src_data.acc_id,trans_message="Amount Transfered to "+str(trg_data.acc_id),amount=amount)
                            db.add(temp)
                            db.commit()
                            sql_query = text("update accounts set balance = :b where cust_id = :a and acc_type = :t")
                            db.execute(sql_query,{"b":trg_balance,"a":cust_id,"t":trg_type})
                            db.commit()
                            temp = Transactions(acc_id=trg_data.acc_id,trans_message="Amount received from "+str(src_data.acc_id),amount=amount)
                            db.add(temp)
                            db.commit()

                            flash(f"Amount transfered to {trg_data.acc_id} from {src_data.acc_id} successfully",'success')
                        else:
                            flash("Insufficient amount to transfer.","danger")
                            
                    else:
                        flash("Accounts not found","danger")

                else:
                    flash("Can't Transfer amount to same account.",'warning')

            else:
                sql_query = text("select * from accounts where cust_id = :a")
                data = db.execute(sql_query,{"a":cust_id}).fetchall()
                if data and len(data) == 2:
                    return render_template('transfer.html', deposit=True, cust_id=cust_id)
                else:
                    flash("Data Not found or Invalid Customer ID",'danger')
                    return redirect(url_for('viewaccount'))

    return redirect(url_for('dashboard'))

# code for view account statment based on the account id
# Using number of last transaction
# or 
# Using Specified date duration
@application.route("/statement" , methods=["GET", "POST"])
def statement():
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] == "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))       
    if session['usert']=="teller" or session['usert']=="cashier":
        if request.method == "POST":
            acc_id = request.form.get("acc_id")
            number = request.form.get("number")
            flag = request.form.get("Radio")
            start_date = request.form.get("start_date")
            end_date = request.form.get("end_date")
            if flag=="red":
                sql_query = text("SELECT * FROM (SELECT * FROM transactions where acc_id=:d ORDER BY trans_id DESC LIMIT :l)Var1 ORDER BY trans_id ASC;")
                data = db.execute(sql_query, {"d": acc_id,"l":number}).fetchall()
            else:
                sql_query = text("SELECT * FROM transactions WHERE acc_id=:a between DATE(time_stamp) >= :s AND DATE(time_stamp) <= :e;")
                data = db.execute(sql_query,{"a":acc_id,"s":start_date,"e":end_date}).fetchall()
            if data:
                return render_template('statement.html', statement=True, data=data, acc_id=acc_id)
            else:
                flash("No Transactions", 'danger')
                return redirect(url_for('dashboard'))
    else:
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))
    return render_template('statement.html', statement=True)

# code for generate Statement PDF or Excel file
@application.route('/pdf_xl_statement/<acc_id>')
@application.route('/pdf_xl_statement/<acc_id>/<ftype>')
def pdf_xl_statement(acc_id=None,ftype=None):
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['usert'] == "executive":
        flash("You don't have access to this page","warning")
        return redirect(url_for('dashboard'))       
    if session['usert']=="teller" or session['usert']=="cashier":
        if acc_id is not None:
            sql_query = text("SELECT * FROM transactions WHERE acc_id=:a order by time_stamp limit 20;")
            data = db.execute(sql_query,{"a":acc_id}).fetchall()
            column_names = ['TransactionId', 'Description', 'Date', 'Amount']
            if data:
                if ftype is None: # Check for provide pdf file as default
                    pdf = FPDF()
                    pdf.add_page()
                    
                    page_width = pdf.w - 2 * pdf.l_margin
                    
                    # code for setting header
                    pdf.set_font('Times','B',16.0) 
                    pdf.cell(page_width, 0.0, "Retail Banking", align='C')
                    pdf.ln(10)

                    # code for Showing account id
                    msg='Account Statment : '+str(acc_id)
                    pdf.set_font('Times','',12.0) 
                    pdf.cell(page_width, 0.0, msg, align='C')
                    pdf.ln(10)

                    # code for Showing account id
                    pdf.set_font('Times', 'B', 11)
                    pdf.ln(1)
                    
                    th = pdf.font_size
                    
                    # code for table header
                    pdf.cell(page_width/5, th, 'Transaction Id')
                    pdf.cell(page_width/3, th, 'Description')
                    pdf.cell(page_width/3, th, 'Date')
                    pdf.cell(page_width/7, th, 'Amont')
                    pdf.ln(th)

                    pdf.set_font('Times', '', 11)

                    # code for table row data
                    for row in data:
                        pdf.cell(page_width/5, th, str(row.trans_id))
                        pdf.cell(page_width/3, th, row.trans_message)
                        pdf.cell(page_width/3, th, str(row.time_stamp))
                        pdf.cell(page_width/7, th, str(row.amount))
                        pdf.ln(th)
                    
                    pdf.ln(10)
                    sql_query = text("SELECT balance FROM accounts WHERE acc_id=:a;")
                    bal = db.execute(sql_query,{"a":acc_id}).fetchone()
                    
                    pdf.set_font('Times','',10.0) 
                    msg='Current Balance : '+str(bal.balance)
                    pdf.cell(page_width, 0.0, msg, align='C')
                    pdf.ln(5)

                    pdf.cell(page_width, 0.0, '-- End of statement --', align='C')
                    
                    return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'inline;filename=statement.pdf'})
                
                elif ftype == 'xl': # Check for bulid and send Excel file for download

                    output = io.BytesIO()
                    #create WorkBook object
                    workbook = xlwt.Workbook()
                    #add a sheet
                    sh = workbook.add_sheet('Account statment')

                    #add headers
                    sh.write(0, 0, 'Transaction ID')
                    sh.write(0, 1, 'Description')
                    sh.write(0, 2, 'Date')
                    sh.write(0, 3, 'Amount')

                    # add row data into Excel file
                    idx = 0
                    for row in data:
                        sh.write(idx+1, 0, str(row.trans_id))
                        sh.write(idx+1, 1, row.trans_message)
                        sh.write(idx+1, 2, str(row.time_stamp))
                        sh.write(idx+1, 3, str(row.amount))
                        idx += 1

                    workbook.save(output)
                    output.seek(0)

                    response = Response(output, mimetype="application/ms-excel", headers={"Content-Disposition":"attachment;filename=statment.xls"})
                    return response
            else:
                flash("Invalid account Id",'danger')
        else:
            flash("Please, provide account Id",'warning')
    return redirect(url_for('dashboard'))

# route for 404 error
@application.errorhandler(404)
def not_found(e):
  return render_template("404.html") 

# Logout 
@application.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# LOGIN
@application.route("/login", methods=["GET", "POST"])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == "POST":
        usern = request.form.get("username").upper()
        passw = request.form.get("password").encode('utf-8')
        sql_query = text('SELECT * FROM users WHERE id = :u')
        #result = db.execute(sql_query, {"u": usern}).fetchone()
        result = db.query(Users).filter_by(id=usern).first()
        if result is not None:
            if bcrypt.check_password_hash(result.password, passw) is True:
                session['user'] = usern
                session['namet'] = result.name
                session['usert'] = result.user_type
                flash(f"{result.name.capitalize()}, you are successfully logged in!", "success")
                return redirect(url_for('dashboard'))
        flash("Sorry, Username or password not match.","danger")
    return render_template("login.html", login=True)

# Api
@application.route('/api')
@application.route('/api/v1')
def api():
    return """
    <h2>List of Api</h2>
    <ol>
        <li>
            <a href="/api/v1/customerlog">Customer Log</a>
        </li>
    </ol>
    """

# Api for update perticular customer log change in html table onClick of refresh
@application.route('/customerlog', methods=["GET", "POST"])
@application.route('/api/v1/customerlog', methods=["GET", "POST"])
def customerlog():
    if 'user' not in session:
        flash("Please login","warning")
        return redirect(url_for('login'))
    if session['usert'] != "executive":
        flash("You don't have access to this api","warning")
        return redirect(url_for('dashboard'))
    if session['usert']=="executive":
        if request.method == "POST":
            cust_id = request.json['cust_id']
            sql_query = text("select log_message,time_stamp from customerlog where cust_id= :c ORDER by time_stamp desc")
            data = db.execute(sql_query,{'c':cust_id}).fetchone()
            t = {
                    "message" : data.log_message,
                    "date" : data.time_stamp
                }
            return jsonify(t)
        else:
            dict_data = []
            sql_query=text("SELECT customers.cust_id as id, customers.cust_ssn_id as ssn_id, customerlog.log_message as message, customerlog.time_stamp as date from customerlog JOIN customers ON customers.cust_id = customerlog.cust_id order by customerlog.time_stamp desc limit 50")
            data = db.execute(sql_query).fetchall()
            for row in data:
                t = {
                    "id" : row.id,
                    "ssn_id" : row.ssn_id,
                    "message" : row.message,
                    "date" : row.date
                }
                dict_data.append(t)
            return jsonify(dict_data)
    
# Function for pytest
def calculate_balance(current_balance, transaction_amount):
    return current_balance + transaction_amount

# Main
if __name__ == '__main__':
    application.secret_key = 'super_secret_key'
    application.debug = True
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port)
