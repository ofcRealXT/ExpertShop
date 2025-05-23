from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from utils import turkce_format
from dotenv import load_dotenv
import os

load_dotenv()

app= Flask(__name__)
app.secret_key= os.getenv('SECRET_KEY')
app.config["SQLALCHEMY_DATABASE_URI"]= os.getenv('DATABASE_URL')
app.config['IMAGE_UPLOAD_FOLDER']= 'static/uploads/images'
app.config['VIDEO_UPLOAD_FOLDER']= 'static/uploads/videos'


db = SQLAlchemy(app)

image_extensions_allowed= {'png', 'jpg', 'jpeg'}
video_extensions_allowed= {'mp4', 'avi', 'mov', 'webm'}
category_fullnames= {
    "dekorasyon": "Ev & Dekorasyon",
    "elektronik": "Elektronik",
    "spor": "Spor & Outdoor",
    "giyim": "Giyim",
    "kitaplar": "Kitap & Kırtasiye",
    "kozmetik": "Kişisel Bakım & Kozmetik",
    "evcilhayvan": "Evcil Hayvan Ürünleri",
    "diger": "Diğer"
}


# ----------------------------------------------------- Sınıflar -----------------------------------------------------

class User(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    username= db.Column(db.String, unique=True, nullable=False)
    password= db.Column(db.String, nullable=False)
    role= db.Column(db.String, default="user")

class Product(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    name= db.Column(db.Text, nullable=False)
    description= db.Column(db.String, nullable=False)
    price= db.Column(db.Float, nullable=False)
    category_id= db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    seller_id= db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image= db.Column(db.String, nullable=True)
    video= db.Column(db.String, nullable=True)
    sales= db.Column(db.Integer, nullable=False, default=0)
    total_earnings= db.Column(db.Float, nullable=False, default=0)
    stocks= db.Column(db.Integer, nullable=False, default=10)

    comments= db.relationship('Comment', backref="product", cascade="all, delete-orphan", lazy=True)

class Category(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    name= db.Column(db.String(50), nullable=False)

    products= db.relationship('Product', backref="category", lazy=True)

class Cart(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    user_id= db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id= db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity= db.Column(db.Integer, default=1)
    
    user= db.relationship("User", backref="cart_products")
    product= db.relationship("Product", backref="cart_items")

class Comment(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    user_id= db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id= db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    content= db.Column(db.String(300), nullable=False)
    created_at= db.Column(db.String, nullable=False)

    user = db.relationship("User", backref="comments", lazy=True)

class Update(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    title= db.Column(db.String, nullable=False)
    date= db.Column(db.String, nullable=False)
    content= db.Column(db.String(500), nullable=False)

# ----------------------------------------------------- Anasayfa -----------------------------------------------------

@app.route('/')
def home():
    user= None
    if 'user_id' in session:
        user= User.query.get(session['user_id'])
    products= Product.query.all()
    return render_template("home.html", user=user, products=products)

@app.route('/arama', methods=["GET"])
def search():
    query= request.args.get('search-box', '')
    if query:
        products= Product.query.filter(Product.name.ilike(f"%{query}%")).all()
    else:
        products= []
    return render_template("search_results.html", products=products, query=query)

@app.route('/kategori/<string:category_name>')
def category(category_name):
    category= Category.query.filter_by(name=category_name).first()
    if not category:
        category= Category(name=category_name)
        db.session.add(category)
        db.session.commit()

    category_fullname= category_fullnames[category_name]
    products= Product.query.filter_by(category_id=category.id).all()
    return render_template('category_filter.html', category_name=category_name, category_fullname=category_fullname, products=products)

# ----------------------------------------------------- Alışveriş -----------------------------------------------------

@app.route('/sepet')
def cart():
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for("login"))
    
    user_id= session["user_id"]
    cart_products= Cart.query.filter_by(user_id=user_id).all()

    total_price= 0
    for item in cart_products:
        total_price+= item.product.price* item.quantity

    return render_template("cart.html", cart_products=cart_products, total_price=total_price)

@app.route('/sepete_ekle/<int:product_id>')
def add_to_cart(product_id):
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for("login"))
    
    user_id= session["user_id"]
    cart_product= Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_product:
        cart_product.quantity+=1
    else:
        new_cart_product=Cart(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(new_cart_product)
    
    db.session.commit()
    flash("Ürün sepete eklendi!", "success")
    return redirect(url_for("cart"))

@app.route('/sepetten_sil/<int:product_id>')
def remove_from_cart(product_id):
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for("login"))
    
    user_id= session["user_id"]
    cart_product= Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    db.session.delete(cart_product)
    db.session.commit()

    flash("Ürün sepetten silindi.", "success")
    return redirect(url_for("cart"))


@app.route('/sepeti_bosalt')
def empty_cart():
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for("login"))
    user_id= session["user_id"]
    cart_products= Cart.query.filter_by(user_id=user_id).all()

    if not cart_products:
        flash("Sepetiniz boş!", "danger")
        return redirect(url_for("cart"))

    for item in cart_products:
        db.session.delete(item)
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/urunsayisi_azalt/<int:product_id>')
def decrease_quantity(product_id):
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for("login"))
    
    user_id= session["user_id"]
    cart_item= Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if cart_item:
        if cart_item.quantity> 1:
            cart_item.quantity-= 1
        else:
            db.session.delete(cart_item)
        db.session.commit()
    return redirect(url_for('cart'))

@app.route('/urunsayisi_arttir/<int:product_id>')
def increase_quantity(product_id):
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for("login"))

    user_id= session["user_id"]
    cart_item= Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if cart_item:
        cart_item.quantity+=1
    db.session.commit()
    return redirect(url_for("cart"))

# ----------------------------------------------------- Ödeme -----------------------------------------------------

@app.route('/odemeyap', methods=["GET", "POST"])
def payment():
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for("login"))
    user_id= session["user_id"]
    cart_products= Cart.query.filter_by(user_id= user_id)
    total_price=0
    for item in cart_products:
        total_price+= item.product.price* item.quantity

    if request.method== "POST":
        cardnumber= request.form.get('cardnumber')
        expiry_date= request.form.get('expirydate')
        cvc= request.form.get('cvc')

        if not cardnumber or not expiry_date or not cvc:
            flash("Eksik giriş yaptınız!", "danger")
            return redirect(url_for('payment'))

        flash("Ödeme başarılı!", "success")
        return redirect(url_for('complete_purchase'))
    return render_template("payment.html", total_price=total_price)

@app.route('/alisverisi_tamamla')
def complete_purchase():
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for("login"))
    user_id= session["user_id"]
    cart_products= Cart.query.filter_by(user_id=user_id).all()

    if not cart_products:
        flash("Sepetiniz boş!", "danger")
        return redirect(url_for("cart"))
    
    for item in cart_products:
        product= Product.query.get(item.product_id)
        if product:
            product.sales+= item.quantity
            product.total_earnings+= item.quantity* product.price
            product.stocks-= item.quantity
            db.session.delete(item)
        db.session.commit()

    return redirect(url_for('cart'))

# ----------------------------------------------------- Ürünler -----------------------------------------------------

@app.route('/urun_ekle', methods=["GET", "POST"])
def add_product():
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user or user.role != "seller":
        flash("Bu sayfaya erişim izniniz yok!", "danger")
        return redirect(url_for("home"))

    if request.method== "POST":
        name= request.form.get("product_name")
        description= request.form.get("product_desc")
        price= request.form.get("product_price")
        image= request.files.get("product_img")
        video= request.files.get("product_vid")
        category_name= request.form.get("product_category")

        category= Category.query.filter_by(name=category_name).first()
        if not category:
            category= Category(name=category_name)
            db.session.add(category)
            db.session.commit()
        if not name or not description or not price:
            flash("Form'daki tüm alanları doldurun!", "danger")
            return redirect(url_for("add_product"))

        price= float(price)

        product= Product(name= name,
        description=description,
        category_id=category.id,
        price=price,
        seller_id= user.id)

        db.session.add(product)
        db.session.commit()

        image_filename= None
        if image:
            file_ext= image.filename.rsplit('.', 1)[-1].lower()
            if file_ext in image_extensions_allowed:
                image_filename= f"{product.id}.{file_ext}"
                image.save(os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], image_filename))
                product.image= image_filename
                db.session.commit()
            else:
                flash("Bu uzantı uygun değil!", "danger")
                db.session.delete(product)
                db.session.commit()
                return redirect(url_for("add_product"))

        video_filename= None
        if video:
            file_ext= video.filename.rsplit('.', 1)[-1].lower()
            if file_ext in video_extensions_allowed:
                video_filename= f"{product.id}.{file_ext}"
                video.save(os.path.join(app.config['VIDEO_UPLOAD_FOLDER'], video_filename))
                product.video= video_filename
                db.session.commit()
            else:
                flash("Bu uzantı uygun değil!", "danger")
                db.session.delete(product)
                db.session.commit()

                return redirect(url_for("add_product"))
        flash("Ürün başarıyla eklendi!", "success")
        return redirect(url_for("my_shop"))
    return render_template("add_product.html", user=user)

@app.route('/urun/<int:product_id>')
def product_detail(product_id):
    product= Product.query.get_or_404(product_id)
    comments= Comment.query.filter_by(product_id=product.id).all()
    user=None
    if "user_id" in session:
        user_id= session["user_id"]
        user= User.query.filter_by(id= user_id)
    return render_template("product_details.html", product=product, comments=comments, user=user)

@app.route('/urun_sil/<int:product_id>')
def delete_product(product_id):
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for('login'))
    user= User.query.get(session['user_id'])

    if not user or user.role!= "seller":
        flash("Bu sayfaya erişim izniniz yok!", "danger")
        return redirect(url_for("home"))
    
    product= Product.query.get_or_404(product_id)
    if product.image:
        image_location= os.path.join(app.config['UPLOAD_FOLDER'], product.image)
        os.remove(image_location)
    
    Cart.query.filter_by(product_id=product.id).delete()
    
    db.session.delete(product)
    db.session.commit()
    flash("Ürün silindi.", "success")
    return redirect(url_for('my_shop'))

@app.route('/magazam')
def my_shop():
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for('login'))
    
    user= User.query.get(session['user_id'])
    if not user or user.role!= "seller":
        flash("Bu sayfaya erişim izniniz yok!", "danger")
        return redirect(url_for("home"))
    
    products= Product.query.filter_by(seller_id=session['user_id']).all()
    total_revenue= sum([product.total_earnings for product in products])
    return render_template("dashboard.html", products=products, total_revenue=total_revenue)


@app.route('/stok_arttir/<int:product_id>')
def increase_quantity_stocks(product_id):
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for("login"))
    
    user_id= session["user_id"]
    product= Product.query.filter_by(seller_id= user_id, id= product_id).first()
    product.stocks+=1
    db.session.commit()
    return redirect(url_for("my_shop", user_id=user_id, product_id=product_id))

@app.route('/stok_azalt/<int:product_id>')
def decrease_quantity_stocks(product_id):
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for("login"))
    
    user_id= session["user_id"]
    product= Product.query.filter_by(seller_id=user_id, id=product_id).first()

    product.stocks-=1
    db.session.commit()
    return redirect(url_for("my_shop"))

# ----------------------------------------------------- Yorumlar -----------------------------------------------------

@app.route('/yorum_ekle', methods=["POST"])
def add_comment():
    user_id= session["user_id"]
    product_id= request.form.get("product_id")

    content= request.form.get("add-comment")

    created_at= turkce_format(datetime.now())

    comment= Comment(
        user_id= user_id,
        product_id= product_id,
        content= content,
        created_at=created_at
    )
    
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('product_detail', product_id=product_id))

# ----------------------------------------------------- Güncellemeler -----------------------------------------------------

@app.route('/guncellemeler')
def updates():
    user=None
    if "user_id" in session:
        user= User.query.get(session["user_id"])
    
    updates= Update.query.all()

    return render_template("update.html", user=user, updates=updates)

@app.route('/guncelleme_ekle', methods=["GET", "POST"])
def add_update():
    if "user_id" not in session:
        flash("Önce giriş yapmalısınız!", "danger")
        return redirect(url_for('giris'))
    
    user= User.query.get(session["user_id"])
    if user.role=="user" or user.role=="seller":
        flash("Bu sayfaya erişim izniniz yok!", "danger")
        return(redirect(url_for('updates')))

    if request.method== "POST":
        content= request.form.get("update_content")
        title= request.form.get("update_title")
        date= turkce_format(datetime.now())
        new_update= Update(
            title=title,
            date= date,
            content=content
        )

        db.session.add(new_update)
        db.session.commit()
        flash("Güncelleme notu eklendi!", "success")
        return redirect(url_for('updates'))

    return render_template("add_update.html")

# ----------------------------------------------------- Giriş ve Kayıt -----------------------------------------------------

@app.route('/giris', methods=['GET', 'POST'])
def login():
    if request.method== 'POST':
        username= request.form['username']
        password= request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id']= user.id
            flash(f"Hoş geldiniz, {username}!", "success")
            return redirect(url_for('home'))
        flash("Kullanıcı adı veya şifre hatalı!", "danger")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/kayit', methods=["GET", "POST"])
def register():
    if request.method== "POST":
        username= request.form["username"]
        password= request.form["password"]
        role= request.form["role"]
        if not username or not password or not role:
            flash("Kullanıcı adı veya şifre boş olamaz!", "danger")
            return redirect(url_for("register"))
        
        if User.query.filter_by(username=username).first():
            flash("Bu kullanıcı adı zaten alınmış!", "danger")
            return redirect(url_for('register'))
        
        # Şifre güvenliği
        hashed_password= generate_password_hash(password)

        user= User(username=username, password=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()
        flash("Kayıt başarılı! Giriş yapabilirsiniz.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/cikis')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# ----------------------------------------------------- Özel komutlar -----------------------------------------------------

@app.route('/admin', methods=["GET", "POST"])
def admin():
    if "user_id" not in session:
        flash("Giriş yapmalısınız!", "danger")
        return redirect(url_for("login"))
    user_id= session["user_id"]
    user= User.query.filter_by(id= user_id).first()

    if not user or user.role== "seler" or user.role=="user":
        flash(f"Bu sayfaya erişim izniniz yok! Şu anki rolünüz: {user.role}", "danger")
        return redirect(url_for('home'))

    users= User.query.all()
    products= Product.query.all()
    comments= Comment.query.all()

    if request.method== "POST":
        command= request.form.get("command").lower()
        action= request.form.get("action")
        if action== "banuser":
            target_user= User.query.get(command)
            if not target_user:
                flash(f"{command} id'sine sahip bir kullanıcı yok!", "danger")
                return redirect(url_for('admin'))
            
            user_products= Product.query.filter_by(seller_id= target_user.id).all()
            user_comments= Comment.query.filter_by(user_id= target_user.id).all()
            
            for user_comment in user_comments:
                db.session.delete(user_comment)

            for user_product in user_products:
                cart_items= Cart.query.filter_by(product_id= user_product.id).all()
                for item in cart_items:
                    db.session.delete(item)

                db.session.delete(user_product)

            db.session.delete(target_user)
            db.session.commit()
            flash("Kullanıcı engellendi!", "success")
            return redirect(url_for('admin'))                
        elif action== "deleteproduct":
            target_product= Product.query.get(command)
            if not target_product:
                flash(f"{command} sahip bir ürün yok!", "danger")
                return redirect(url_for('admin'))
            cart_items= Cart.query.filter_by(product_id=target_product.id).all()
            for item in cart_items:
                db.session.delete(item)
            db.session.delete(target_product)
            db.session.commit()
            flash("Ürün silindi!", "success")
            return redirect(url_for('admin'))
        elif action== "deletecomment":
            comment= Comment.query.get(command)
            if not comment:
                flash(f"{command} id'sine sahip bir yorum yok!", "danger")
                return redirect(url_for('admin'))
            
            db.session.delete(comment)
            db.session.commit()
            flash("Yorum silindi!", "success")
            return redirect(url_for('admin'))
        elif action== "giveadminrole":
            user= User.query.get(command)
            if not user:
                flash(f"{command} id'sine sahip bir kullanıcı yok!", "danger")
                return redirect(url_for('admin'))
            
            if user.role== "admin":
                flash(f"{user.username} zaten admin rolüne sahip", "success")
                return redirect(url_for('admin'))
            
            
            user.role= "admin"
            user_products= Product.query.filter_by(seller_id= user.id).all()
            db.session.commit()
            flash(f"{user.username} kullanıcısına admin rolü verildi! Rol: {user.role}", "success")
            return redirect(url_for('admin'))
        else:
            if command in ["products", "users", "comments"]:
                if command=="products":
                    for product in products:
                        cart_items = Cart.query.filter_by(product_id=product.id).all()
                        for item in cart_items:
                            db.session.delete(item)
                        db.session.delete(product)

                    db.session.commit()
                    flash("Tüm ürünler silindi!", "success")
                    return redirect(url_for('admin'))
                elif command=="users":
                    users= User.query.all()
                    for user in users:
                        if user.role == "admin":
                            continue
                            
                        user_comments= Comment.query.filter_by(user_id=user.id).all()
                        for user_comment in user_comments:
                            db.session.delete(user_comment)

                        user_products= Product.query.filter_by(seller_id=user.id).all()
                        for user_product in user_products:
                            cart_items = Cart.query.filter_by(product_id=user_product.id).all()
                            for item in cart_items:
                                db.session.delete(item)
                            db.session.delete(user_product)

                        db.session.delete(user)
                    db.session.commit()
                    flash("Tüm kullanıcılar silindi!", "success")
                    return redirect(url_for('admin'))
                else:
                    for comment in comments:
                        db.session.delete(comment)
                    db.session.commit()
                    flash("Tüm yorumlar silindi!", "success")
                    return redirect(url_for('admin'))
            else:
                flash("Bu komut geçersiz", "danger")    
                return redirect(url_for('admin'))
    
    return render_template("admin.html", users=users, products=products, comments=comments)

if __name__ == "__main__":
    app.run(debug=True)
    #app.run(host="0.0.0.0", port=5000, debug=True) # Aynı ip'deki cihazların girebilmesi için
