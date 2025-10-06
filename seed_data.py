from app import app, db, Product, Location, ProductMovement
from datetime import datetime, timedelta
import random

def seed_database():
    """Seed the database with sample data"""
    with app.app_context():

        db.create_all()
        

        try:
            ProductMovement.query.delete()
            Product.query.delete()
            Location.query.delete()
            db.session.commit()
        except:

            pass
        
        # Products
        products = [
            Product(product_id='PROD001', name='Laptop', description='High-performance laptop for business use'),
            Product(product_id='PROD002', name='Desktop Computer', description='Desktop computer for office work'),
            Product(product_id='PROD003', name='Monitor', description='24-inch LCD monitor'),
            Product(product_id='PROD004', name='Keyboard', description='Wireless keyboard'),
        ]
        
        for product in products:
            db.session.add(product)
        
        # Locations
        locations = [
            Location(location_id='WH001', name='Main Warehouse', address='123 Industrial Blvd, Business District'),
            Location(location_id='WH002', name='Secondary Warehouse', address='456 Storage Ave, Industrial Zone'),
            Location(location_id='STORE01', name='Downtown Store', address='789 Main St, Downtown'),
            Location(location_id='STORE02', name='Mall Store', address='321 Shopping Center, Mall Plaza'),
        ]
        
        for location in locations:
            db.session.add(location)
        
        db.session.commit()
        

        movements = []
        
        # Stock in operations 
        stock_in_movements = [
            ('MOV001', 'PROD001', None, 'WH001', 50),
            ('MOV002', 'PROD002', None, 'WH001', 30),
            ('MOV003', 'PROD003', None, 'WH001', 100),
            ('MOV004', 'PROD004', None, 'WH001', 200),
            ('MOV005', 'PROD001', None, 'WH002', 25),
            ('MOV006', 'PROD002', None, 'WH002', 15),
            ('MOV007', 'PROD003', None, 'WH002', 50),
            ('MOV008', 'PROD004', None, 'WH002', 100),
        ]
        
        # Transfer operations (moving between locations)
        transfer_movements = [
            ('MOV009', 'PROD001', 'WH001', 'STORE01', 10),
            ('MOV010', 'PROD002', 'WH001', 'STORE01', 5),
            ('MOV011', 'PROD003', 'WH001', 'STORE01', 20),
            ('MOV012', 'PROD004', 'WH001', 'STORE01', 50),
            ('MOV013', 'PROD001', 'WH002', 'STORE02', 8),
            ('MOV014', 'PROD002', 'WH002', 'STORE02', 3),
            ('MOV015', 'PROD003', 'WH002', 'STORE02', 15),
            ('MOV016', 'PROD004', 'WH002', 'STORE02', 30),
        ]
        
        # Stock out operations (removing inventory from locations)
        stock_out_movements = [
            ('MOV017', 'PROD001', 'STORE01', None, 3),
            ('MOV018', 'PROD002', 'STORE01', None, 2),
            ('MOV019', 'PROD003', 'STORE01', None, 5),
            ('MOV020', 'PROD004', 'STORE01', None, 10),
        ]
        
        # Combine all movements
        all_movements = stock_in_movements + transfer_movements + stock_out_movements
        
        # Create movement records with timestamps
        base_time = datetime.now() - timedelta(days=30)
        
        for i, (mov_id, product_id, from_loc, to_loc, qty) in enumerate(all_movements):

            timestamp = base_time + timedelta(days=random.randint(0, 29), 
                                            hours=random.randint(8, 17),
                                            minutes=random.randint(0, 59))
            
            movement = ProductMovement(
                movement_id=mov_id,
                timestamp=timestamp,
                from_location=from_loc,
                to_location=to_loc,
                product_id=product_id,
                qty=qty
            )
            movements.append(movement)
        

        movements.sort(key=lambda x: x.timestamp)
        
        for movement in movements:
            db.session.add(movement)
        
        db.session.commit()
        
        print("Database seeded successfully!")
        print(f"Created {len(products)} products")
        print(f"Created {len(locations)} locations")
        print(f"Created {len(movements)} movements")
        
        print("\nCurrent stock levels:")
        for location in locations:
            print(f"\n{location.name} ({location.location_id}):")
            for product in products:
                incoming = db.session.query(db.func.sum(ProductMovement.qty)).filter(
                    ProductMovement.product_id == product.product_id,
                    ProductMovement.to_location == location.location_id
                ).scalar() or 0
                
                outgoing = db.session.query(db.func.sum(ProductMovement.qty)).filter(
                    ProductMovement.product_id == product.product_id,
                    ProductMovement.from_location == location.location_id
                ).scalar() or 0
                
                balance = incoming - outgoing
                if balance != 0:
                    print(f"  {product.product_id}: {balance} units")

if __name__ == '__main__':
    print("Setting up your inventory database with sample data...")
    print("This will create products, locations, and movements for you to try!")
    print("=" * 60)
    seed_database()
    print("=" * 60)
    print("All done! You can now run 'python3 app.py' to start your app!")
    print("Then visit: http://127.0.0.1:5001 in your browser")