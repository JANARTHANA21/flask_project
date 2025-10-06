from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__, template_folder='views')
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models -> Schema 
class Product(db.Model):
    product_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Product {self.product_id}: {self.name}>'

class Location(db.Model):
    location_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Location {self.location_id}: {self.name}>'

class ProductMovement(db.Model):
    movement_id = db.Column(db.String(50), primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    from_location = db.Column(db.String(50), db.ForeignKey('location.location_id'), nullable=True)
    to_location = db.Column(db.String(50), db.ForeignKey('location.location_id'), nullable=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.product_id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref=db.backref('movements', lazy=True))
    from_loc = db.relationship('Location', foreign_keys=[from_location], backref=db.backref('outgoing_movements', lazy=True))
    to_loc = db.relationship('Location', foreign_keys=[to_location], backref=db.backref('incoming_movements', lazy=True))
    
    def validate_movement(self):
        errors = []
        

        if not self.from_location and not self.to_location:
            errors.append("At least one location (from or to) must be specified")
        

        if self.qty <= 0:
            errors.append("Quantity must be greater than 0")
        

        if self.from_location and self.to_location and self.from_location == self.to_location:
            errors.append("Cannot move from and to the same location")
        
        return errors
    
    def get_movement_type(self):

        if self.to_location and not self.from_location:
            return "Stock In"
        elif self.from_location and not self.to_location:
            return "Stock Out"
        else:
            return "Transfer"
    
    def __repr__(self):
        return f'<Movement {self.movement_id}: {self.product_id} - {self.qty}>'

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Product Routes
@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products/index.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_id = request.form['product_id']
        name = request.form['name']
        description = request.form['description']
        

        if Product.query.get(product_id):
            flash('Product ID already exists!', 'error')
            return render_template('products/add.html')
        
        product = Product(product_id=product_id, name=name, description=description)
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))
    
    return render_template('products/add.html')

@app.route('/products/edit/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))
    
    return render_template('products/edit.html', product=product)

@app.route('/products/view/<product_id>')
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    movements = ProductMovement.query.filter_by(product_id=product_id).order_by(ProductMovement.timestamp.desc()).all()
    return render_template('products/view.html', product=product, movements=movements)

# Location Routes
@app.route('/locations')
def locations():
    locations = Location.query.all()
    return render_template('locations/index.html', locations=locations)

@app.route('/locations/add', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        location_id = request.form['location_id']
        name = request.form['name']
        address = request.form['address']
        

        if Location.query.get(location_id):
            flash('Location ID already exists!', 'error')
            return render_template('locations/add.html')
        
        location = Location(location_id=location_id, name=name, address=address)
        db.session.add(location)
        db.session.commit()
        flash('Location added successfully!', 'success')
        return redirect(url_for('locations'))
    
    return render_template('locations/add.html')

@app.route('/locations/edit/<location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    location = Location.query.get_or_404(location_id)
    
    if request.method == 'POST':
        location.name = request.form['name']
        location.address = request.form['address']
        db.session.commit()
        flash('Location updated successfully!', 'success')
        return redirect(url_for('locations'))
    
    return render_template('locations/edit.html', location=location)

@app.route('/locations/view/<location_id>')
def view_location(location_id):
    location = Location.query.get_or_404(location_id)
    incoming_movements = ProductMovement.query.filter_by(to_location=location_id).order_by(ProductMovement.timestamp.desc()).all()
    outgoing_movements = ProductMovement.query.filter_by(from_location=location_id).order_by(ProductMovement.timestamp.desc()).all()
    return render_template('locations/view.html', location=location, 
                         incoming_movements=incoming_movements, outgoing_movements=outgoing_movements)

# Movement Routes
@app.route('/movements')
def movements():
    movements = ProductMovement.query.order_by(ProductMovement.timestamp.desc()).all()
    return render_template('movements/index.html', movements=movements)

@app.route('/movements/add', methods=['GET', 'POST'])
def add_movement():
    if request.method == 'POST':
        movement_id = request.form['movement_id']
        from_location = request.form.get('from_location') or None
        to_location = request.form.get('to_location') or None
        product_id = request.form['product_id']
        
        try:
            qty = int(request.form['qty'])
        except (ValueError, TypeError):
            flash('Quantity must be a valid number!', 'error')
            return render_template('movements/add.html', products=Product.query.all(), locations=Location.query.all())
        

        if ProductMovement.query.get(movement_id):
            flash('Movement ID already exists!', 'error')
            return render_template('movements/add.html', products=Product.query.all(), locations=Location.query.all())
        

        movement = ProductMovement(
            movement_id=movement_id,
            from_location=from_location,
            to_location=to_location,
            product_id=product_id,
            qty=qty
        )
        

        validation_errors = movement.validate_movement()
        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
            return render_template('movements/add.html', products=Product.query.all(), locations=Location.query.all())
        

        try:
            db.session.add(movement)
            db.session.commit()
            movement_type = movement.get_movement_type()
            flash(f'{movement_type} movement added successfully!', 'success')
            return redirect(url_for('movements'))
        except Exception as e:
            db.session.rollback()
            flash('Error saving movement. Please try again.', 'error')
            return render_template('movements/add.html', products=Product.query.all(), locations=Location.query.all())
    
    products = Product.query.all()
    locations = Location.query.all()
    return render_template('movements/add.html', products=products, locations=locations)

@app.route('/movements/edit/<movement_id>', methods=['GET', 'POST'])
def edit_movement(movement_id):
    movement = ProductMovement.query.get_or_404(movement_id)
    
    if request.method == 'POST':

        original_values = {
            'from_location': movement.from_location,
            'to_location': movement.to_location,
            'product_id': movement.product_id,
            'qty': movement.qty
        }
        
        from_location = request.form.get('from_location') or None
        to_location = request.form.get('to_location') or None
        product_id = request.form['product_id']
        
        try:
            qty = int(request.form['qty'])
        except (ValueError, TypeError):
            flash('Quantity must be a valid number!', 'error')
            return render_template('movements/edit.html', movement=movement, 
                                 products=Product.query.all(), locations=Location.query.all())
        

        movement.from_location = from_location
        movement.to_location = to_location
        movement.product_id = product_id
        movement.qty = qty
        

        validation_errors = movement.validate_movement()
        if validation_errors:

            movement.from_location = original_values['from_location']
            movement.to_location = original_values['to_location']
            movement.product_id = original_values['product_id']
            movement.qty = original_values['qty']
            
            for error in validation_errors:
                flash(error, 'error')
            return render_template('movements/edit.html', movement=movement, 
                                 products=Product.query.all(), locations=Location.query.all())
        

        try:
            db.session.commit()
            movement_type = movement.get_movement_type()
            flash(f'{movement_type} movement updated successfully!', 'success')
            return redirect(url_for('movements'))
        except Exception as e:
            db.session.rollback()

            movement.from_location = original_values['from_location']
            movement.to_location = original_values['to_location']
            movement.product_id = original_values['product_id']
            movement.qty = original_values['qty']
            
            flash('Error updating movement. Please try again.', 'error')
            return render_template('movements/edit.html', movement=movement, 
                                 products=Product.query.all(), locations=Location.query.all())
    
    products = Product.query.all()
    locations = Location.query.all()
    return render_template('movements/edit.html', movement=movement, products=products, locations=locations)

@app.route('/movements/view/<movement_id>')
def view_movement(movement_id):
    movement = ProductMovement.query.get_or_404(movement_id)
    return render_template('movements/view.html', movement=movement)

# Reports
@app.route('/reports/balance')
def balance_report():

    balance_data = []
    
    products = Product.query.all()
    locations = Location.query.all()
    
    for product in products:
        for location in locations:

            incoming_query = db.session.query(db.func.sum(ProductMovement.qty)).filter(
                ProductMovement.product_id == product.product_id,
                ProductMovement.to_location == location.location_id
            )
            incoming_qty = incoming_query.scalar() or 0
            

            outgoing_query = db.session.query(db.func.sum(ProductMovement.qty)).filter(
                ProductMovement.product_id == product.product_id,
                ProductMovement.from_location == location.location_id
            )
            outgoing_qty = outgoing_query.scalar() or 0
            

            balance = incoming_qty - outgoing_qty
            

            if balance != 0:
                balance_data.append({
                    'product_id': product.product_id,
                    'product_name': product.name,
                    'location_id': location.location_id,
                    'location_name': location.name,
                    'balance': balance
                })
    

    balance_data.sort(key=lambda x: (x['product_id'], x['location_id']))
    
    return render_template('reports/balance.html', balance_data=balance_data)

if __name__ == '__main__':
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Start the Flask app
    print("Starting Flask Inventory App...")
    print("Visit: http://127.0.0.1:5002")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    app.run(debug=True, port=5002)