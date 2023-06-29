import httplib2
from bs4 import BeautifulSoup
import requests
from flask import Flask, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = "super-secret-key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['STATIC_FOLDER'] = 'templates'
app.config['SAVED_ITEMS_DATABASE_URI'] = 'sqlite:///saved_items.db'
db = SQLAlchemy(app)
http = httplib2.Http()


class Category:
    def __init__(self, name, url, image):
        self.name = name
        self.url = url
        self.image = image


categories = [
    Category("Łożyska kulkowe", "/category/lozyska-kulkowe", "2.jpg"),
    # Dodaj więcej kategorii
]


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    specification = db.Column(db.String(200))
    stock = db.Column(db.Integer)
    price = db.Column(db.Float)
    currency = db.Column(db.String(20))


class SavedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer)
    full_name = db.Column(db.String(100))
    specification = db.Column(db.String(200))
    stock = db.Column(db.Float)
    price = db.Column(db.Float)
    currency = db.Column(db.String(20))


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer)
    full_name = db.Column(db.String(100))
    specification = db.Column(db.String(200))
    stock = db.Column(db.Float)
    price = db.Column(db.Float)
    currency = db.Column(db.String(20))
    total_price = db.Column(db.Float)


class PurchasedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer)
    full_name = db.Column(db.String(100))
    specification = db.Column(db.String(200))
    stock = db.Column(db.Float)
    price = db.Column(db.Float)
    currency = db.Column(db.String(20))


def initialize_saved_items_database():
    with app.app_context():
        db.create_all()
        SavedItem.__table__.create(db.engine, checkfirst=True)


# Wywołanie funkcji initialize_saved_items_database
initialize_saved_items_database()

with app.app_context():
    db.create_all()
    # Adres URL strony, z której chcesz pobrać dane
    url = 'https://b2b.rombor.com.pl/1106-zwykle-lozyska-kulkowe'

    # Wykonaj żądanie GET na stronie
    response = requests.get(url)

    # Sprawdź kod odpowiedzi - 200 oznacza sukces
    if response.status_code == 200:
        # Pobierz zawartość strony
        content = response.content

        # Utwórz obiekt BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')

        # Przykład: Wyodrębnij wszystkie interesujące wartości
        product_containers = soup.find_all('div', class_='product-container')

        # Inicjalizuj pustą listę na wyniki
        results = []

        for product_container in product_containers:
            product_name = product_container.find('a', class_='product-name').text.strip()
            product_dimensions = product_container.find('p', class_="product-desc").text.strip()
            stock_info = product_container.find('div', class_="stany").text.strip()
            actual_price = product_container.find('span', class_="price product-price").text.strip()

            # Usuń niechciane znaki z ceny
            actual_price = actual_price.replace(',', '.').replace('zł', '').strip()

            # Usuń tekst po frazie "Stany magazynowe Centralny:"
            stock_info = stock_info.split('Stany magazynowe Centralny:')[1].split('szt.')[0].strip()
            if 'Kłobuck:' in stock_info:
                continue

            result = f'{product_name} - {product_dimensions} - Stany magazynowe Centralny: {stock_info} szt. - {actual_price}'
            results.append(result)

            product = Product(
                full_name=product_name,
                specification=product_dimensions,
                stock=int(stock_info),
                price=float(actual_price),
                currency='zł'  # Dodaj jednostkę (jeśli dostępna)
            )
            db.session.add(product)

        db.session.commit()  # Zatwierdź zmiany w bazie danych

        # print(results)
    else:
        print('Błąd podczas pobierania strony:', response.status_code)

@app.route('/')
def index():
    return render_template('index.html', categories=categories)


@app.route('/products', methods=["GET", "POST"])
def products():
    if request.form:
        full_name = request.form.get("full_name")
        specification = request.form.get("specification")
        stock = request.form.get("stock")
        price = request.form.get("price")
        currency = request.form.get("currency")
        product_one = Product(full_name=full_name, specification=specification, stock=stock,
                              price=price, currency=currency)
        with app.app_context():
            try:
                db.session.add(product_one)
                db.session.commit()
                flash("Zaimportowano dane!")
            except:
                flash("Nie można przenieść danych!")
    product_data = Product.query.all()  # Pobranie danych z bazy danych
    return render_template("product_categories.html", products=product_data)


@app.route('/category/lozyska-kulkowe')
def lozyska_kulkowe():
    return redirect('/products')


@app.route('/product_categories')
def product_categories():
    return redirect('/products')


@app.route('/save_items/<int:product_id>', methods=["GET", "POST"])
def save_items(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = None
    if request.method == "POST":
        quantity = request.form.get("quantity")
        item = SavedItem(
            product_id=product.id,
            full_name=product.full_name,
            specification=product.specification,
            stock=quantity,
            price=product.price,
            currency=product.currency
        )
        product.stock -= int(quantity)
        db.session.add(item)
        db.session.commit()
        flash("Item saved successfully!")

    items = SavedItem.query.all()  # Pobierz elementy zapisane w bazie danych

    return render_template("save_items.html", product=product, quantity=float(quantity), items=items)


@app.route('/zakupione')
def zakupione():
    purchased_products = SavedItem.query.all()
    return render_template('zakupione.html', purchased_products=purchased_products)


if __name__ == '__main__':
    app.run(debug=True)
