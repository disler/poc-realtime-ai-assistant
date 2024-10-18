-- DuckDB SQL Script to Create Tables and Insert Data

-- Creating Users table with additional columns
CREATE TABLE Users (
    UserID INTEGER NOT NULL PRIMARY KEY,
    FirstName VARCHAR(100) NOT NULL,
    LastName VARCHAR(100) NOT NULL,
    Email VARCHAR(255) NOT NULL UNIQUE,
    Address VARCHAR(255),
    City VARCHAR(100),
    State VARCHAR(50),
    ZipCode VARCHAR(20),
    Country VARCHAR(100),
    PhoneNumber VARCHAR(20),
    RegistrationDate DATE
);

-- Insert sample data into Users table
INSERT INTO Users (UserID, FirstName, LastName, Email, Address, City, State, ZipCode, Country, PhoneNumber, RegistrationDate) VALUES
(1, 'John', 'Doe', 'john.doe@example.com', '123 Main St', 'Springfield', 'IL', '62704', 'USA', '555-123-4567', '2021-01-15'),
(2, 'Jane', 'Roe', 'jane.roe@example.com', '456 Elm St', 'Metropolis', 'NY', '10001', 'USA', '555-234-5678', '2021-02-20'),
(3, 'Alice', 'Smith', 'alice.smith@example.com', '789 Oak St', 'Gotham', 'NJ', '07030', 'USA', '555-345-6789', '2021-03-05'),
(4, 'Bob', 'Johnson', 'bob.johnson@example.com', '101 Maple St', 'Smallville', 'KS', '66002', 'USA', '555-456-7890', '2021-04-10'),
(5, 'Carol', 'Williams', 'carol.williams@example.com', '202 Pine St', 'Star City', 'CA', '95050', 'USA', '555-567-8901', '2021-05-15'),
(6, 'David', 'Brown', 'david.brown@example.com', '303 Cedar St', 'Central City', 'MO', '64030', 'USA', '555-678-9012', '2021-06-20'),
(7, 'Eve', 'Davis', 'eve.davis@example.com', '404 Birch St', 'Coast City', 'CA', '92627', 'USA', '555-789-0123', '2021-07-25'),
(8, 'Frank', 'Miller', 'frank.miller@example.com', '505 Walnut St', 'Bludhaven', 'NJ', '07002', 'USA', '555-890-1234', '2021-08-30'),
(9, 'Grace', 'Wilson', 'grace.wilson@example.com', '606 Cherry St', 'Fawcett City', 'MA', '01720', 'USA', '555-901-2345', '2021-09-05'),
(10, 'Hank', 'Moore', 'hank.moore@example.com', '707 Ash St', 'Hub City', 'SD', '57034', 'USA', '555-012-3456', '2021-10-10'),
(11, 'Ivy', 'Taylor', 'ivy.taylor@example.com', '808 Spruce St', 'Keystone City', 'PA', '16159', 'USA', '555-123-4567', '2021-11-15'),
(12, 'Jack', 'Anderson', 'jack.anderson@example.com', '909 Poplar St', 'Opal City', 'MD', '20630', 'USA', '555-234-5678', '2021-12-20'),
(13, 'Karen', 'Thomas', 'karen.thomas@example.com', '1010 Fir St', 'Midway City', 'MI', '49047', 'USA', '555-345-6789', '2022-01-25'),
(14, 'Leo', 'Jackson', 'leo.jackson@example.com', '1111 Cypress St', 'Ivy Town', 'PA', '19390', 'USA', '555-456-7890', '2022-02-28'),
(15, 'Mia', 'White', 'mia.white@example.com', '1212 Magnolia St', 'Happy Harbor', 'RI', '02835', 'USA', '555-567-8901', '2022-03-05'),
(16, 'Nick', 'Harris', 'nick.harris@example.com', '1313 Willow St', 'Amnesty Bay', 'ME', '04406', 'USA', '555-678-9012', '2022-04-10'),
(17, 'Olivia', 'Martin', 'olivia.martin@example.com', '1414 Palm St', 'Gateway City', 'CA', '94102', 'USA', '555-789-0123', '2022-05-15'),
(18, 'Paul', 'Thompson', 'paul.thompson@example.com', '1515 Dogwood St', 'New Carthage', 'TX', '75633', 'USA', '555-890-1234', '2022-06-20'),
(19, 'Quincy', 'Garcia', 'quincy.garcia@example.com', '1616 Sycamore St', 'San Diego', 'CA', '92101', 'USA', '555-901-2345', '2022-07-25'),
(20, 'Rachel', 'Martinez', 'rachel.martinez@example.com', '1717 Hickory St', 'Los Angeles', 'CA', '90001', 'USA', '555-012-3456', '2022-08-30'),
(21, 'Sam', 'Robinson', 'sam.robinson@example.com', '1818 Redwood St', 'Seattle', 'WA', '98101', 'USA', '555-123-4567', '2022-09-05'),
(22, 'Tina', 'Clark', 'tina.clark@example.com', '1919 Alder St', 'Portland', 'OR', '97201', 'USA', '555-234-5678', '2022-10-10'),
(23, 'Uma', 'Lewis', 'uma.lewis@example.com', '2020 Beech St', 'Denver', 'CO', '80014', 'USA', '555-345-6789', '2022-11-15'),
(24, 'Victor', 'Lee', 'victor.lee@example.com', '2121 Maple St', 'Austin', 'TX', '73301', 'USA', '555-456-7890', '2022-12-20'),
(25, 'Wendy', 'Walker', 'wendy.walker@example.com', '2222 Pine St', 'Boston', 'MA', '02108', 'USA', '555-567-8901', '2023-01-25'),
(26, 'Xavier', 'Hall', 'xavier.hall@example.com', '2323 Cedar St', 'Chicago', 'IL', '60601', 'USA', '555-678-9012', '2023-02-28'),
(27, 'Yara', 'Allen', 'yara.allen@example.com', '2424 Birch St', 'Houston', 'TX', '77001', 'USA', '555-789-0123', '2023-03-05'),
(28, 'Zack', 'Young', 'zack.young@example.com', '2525 Walnut St', 'Phoenix', 'AZ', '85001', 'USA', '555-890-1234', '2023-04-10'),
(29, 'Amy', 'King', 'amy.king@example.com', '2626 Cherry St', 'Philadelphia', 'PA', '19019', 'USA', '555-901-2345', '2023-05-15'),
(30, 'Brian', 'Scott', 'brian.scott@example.com', '2727 Ash St', 'San Antonio', 'TX', '78201', 'USA', '555-012-3456', '2023-06-20'),
(31, 'Cindy', 'Green', 'cindy.green@example.com', '2828 Spruce St', 'San Jose', 'CA', '95101', 'USA', '555-123-4567', '2023-07-25'),
(32, 'Derek', 'Adams', 'derek.adams@example.com', '2929 Poplar St', 'Dallas', 'TX', '75201', 'USA', '555-234-5678', '2023-08-30'),
(33, 'Emma', 'Baker', 'emma.baker@example.com', '3030 Fir St', 'San Francisco', 'CA', '94101', 'USA', '555-345-6789', '2023-09-05'),
(34, 'Franklin', 'Nelson', 'franklin.nelson@example.com', '3131 Cypress St', 'Columbus', 'OH', '43085', 'USA', '555-456-7890', '2023-10-10'),
(35, 'Grace', 'Hill', 'grace.hill@example.com', '3232 Magnolia St', 'Charlotte', 'NC', '28201', 'USA', '555-567-8901', '2023-11-15'),
(36, 'Henry', 'Edwards', 'henry.edwards@example.com', '3333 Willow St', 'Fort Worth', 'TX', '76101', 'USA', '555-678-9012', '2023-12-20'),
(37, 'Isla', 'Collins', 'isla.collins@example.com', '3434 Palm St', 'Detroit', 'MI', '48201', 'USA', '555-789-0123', '2024-01-25'),
(38, 'Jack', 'Stewart', 'jack.stewart@example.com', '3535 Dogwood St', 'El Paso', 'TX', '79901', 'USA', '555-890-1234', '2024-02-28'),
(39, 'Kara', 'Simmons', 'kara.simmons@example.com', '3636 Sycamore St', 'Memphis', 'TN', '37501', 'USA', '555-901-2345', '2024-03-05'),
(40, 'Liam', 'Patterson', 'liam.patterson@example.com', '3737 Hickory St', 'Nashville', 'TN', '37201', 'USA', '555-012-3456', '2024-04-10'),
(41, 'Mia', 'Reed', 'mia.reed@example.com', '3838 Redwood St', 'Baltimore', 'MD', '21201', 'USA', '555-123-4567', '2024-05-15'),
(42, 'Noah', 'Kelly', 'noah.kelly@example.com', '3939 Alder St', 'Louisville', 'KY', '40201', 'USA', '555-234-5678', '2024-06-20');

-- Creating Categories table
CREATE TABLE Categories (
    CategoryID INTEGER NOT NULL PRIMARY KEY,
    CategoryName VARCHAR(255) NOT NULL
);

-- Insert sample data into Categories table
INSERT INTO Categories (CategoryID, CategoryName) VALUES
(1, 'Laptops'),
(2, 'Desktops'),
(3, 'Graphics Cards'),
(4, 'Storage'),
(5, 'Accessories'),
(6, 'Software'),
(7, 'Mobile Devices'),
(8, 'Virtual Reality'),
(9, 'Gaming'),
(10, 'Cameras'),
(11, 'Networking'),
(12, 'Wearables'),
(13, 'Displays'),
(14, 'Audio'),
(15, 'Office Supplies'),
(16, 'Cables'),
(17, 'Input Devices'),
(18, 'Power Devices'),
(19, 'Security Devices'),
(20, 'Smart Home'),
(21, 'Health Tech');

-- Creating Products table with updated products
CREATE TABLE Products (
    ProductID INTEGER NOT NULL PRIMARY KEY,
    ProductName VARCHAR(255) NOT NULL,
    Price DECIMAL(10, 2) NOT NULL,
    CategoryID INTEGER REFERENCES Categories(CategoryID)
);

-- Insert sample data into Products table
INSERT INTO Products (ProductID, ProductName, Price, CategoryID) VALUES
(1, 'MacBook Air M1', 999.99, 1),
(2, 'MacBook Pro M2', 2299.99, 1),
(3, 'MacBook Pro M3', 3499.99, 1),
(4, 'MacBook Pro M4', 4699.99, 1),
(5, 'Apple Vision Pro', 4499.99, 8),
(6, 'Nvidia GeForce RTX 3080', 699.99, 3),
(7, 'Nvidia GeForce RTX 3090', 1499.99, 3),
(8, 'Nvidia GeForce RTX 4080', 1199.99, 3),
(9, 'Nvidia GeForce RTX 4090', 1599.99, 3),
(10, 'Samsung 980 Pro 1TB SSD', 199.99, 4),
(11, 'WD Black SN850 1TB SSD', 229.99, 4),
(12, 'Cyberpunk 2077 (PC)', 59.99, 9),
(13, 'Call of Duty: Modern Warfare II (PC)', 59.99, 9),
(14, 'PlayStation 5', 499.99, 9),
(15, 'Xbox Series X', 499.99, 9),
(16, 'Dell UltraSharp 27" Monitor', 449.99, 13),
(17, 'Logitech MX Master 3 Mouse', 99.99, 17),
(18, 'Razer Huntsman Elite Keyboard', 199.99, 17),
(19, 'Bose QuietComfort 35 II Headphones', 299.99, 14),
(20, 'Samsung Galaxy S21 Ultra', 1199.99, 7),
(21, 'Apple iPhone 13 Pro Max', 1099.99, 7),
(22, 'Google Pixel 6 Pro', 899.99, 7),
(23, 'Amazon Echo Dot (4th Gen)', 49.99, 20),
(24, 'Philips Hue Smart Bulb', 14.99, 20),
(25, 'Ring Video Doorbell Pro', 249.99, 19),
(26, 'Fitbit Charge 5', 179.99, 12),
(27, 'Apple Watch Series 7', 399.99, 12),
(28, 'Microsoft Office 365 Subscription', 99.99, 6),
(29, 'Adobe Photoshop CC Subscription', 239.88, 6),
(30, 'Anker PowerCore 20100mAh Power Bank', 49.99, 18),
(31, 'Seagate 4TB External Hard Drive', 99.99, 4),
(32, 'NETGEAR Nighthawk WiFi 6 Router', 299.99, 11),
(33, 'Oculus Quest 2 VR Headset', 299.99, 8),
(34, 'Norton 360 Deluxe', 49.99, 6),
(35, 'Kaspersky Total Security', 79.99, 6),
(36, 'Nintendo Switch', 299.99, 9),
(37, 'Asus ROG Gaming Laptop', 1499.99, 1),
(38, 'Alienware Aurora Gaming Desktop', 1799.99, 2),
(39, 'HP Envy 13 Laptop', 999.99, 1),
(40, 'Logitech C920 HD Pro Webcam', 79.99, 10),
(41, 'Canon EOS Rebel T7 DSLR Camera', 449.99, 10),
(42, 'JBL Flip 5 Bluetooth Speaker', 119.99, 14);

-- Creating Orders table
CREATE TABLE Orders (
    OrderID INTEGER NOT NULL PRIMARY KEY,
    OrderDate DATE NOT NULL,
    UserID INTEGER NOT NULL REFERENCES Users(UserID)
);

-- Insert sample data into Orders table
INSERT INTO Orders (OrderID, OrderDate, UserID) VALUES
(1, '2023-01-15', 1),
(2, '2023-01-16', 2),
(3, '2023-01-17', 3),
(4, '2023-01-18', 4),
(5, '2023-01-19', 5),
(6, '2023-01-20', 6),
(7, '2023-01-21', 7),
(8, '2023-01-22', 8),
(9, '2023-01-23', 9),
(10, '2023-01-24', 10),
(11, '2023-01-25', 11),
(12, '2023-01-26', 12),
(13, '2023-01-27', 13),
(14, '2023-01-28', 14),
(15, '2023-01-29', 15),
(16, '2023-01-30', 16),
(17, '2023-01-31', 17),
(18, '2023-02-01', 18),
(19, '2023-02-02', 19),
(20, '2023-02-03', 20),
(21, '2023-02-04', 21),
(22, '2023-02-05', 22),
(23, '2023-02-06', 23),
(24, '2023-02-07', 24),
(25, '2023-02-08', 25),
(26, '2023-02-09', 26),
(27, '2023-02-10', 27),
(28, '2023-02-11', 28),
(29, '2023-02-12', 29),
(30, '2023-02-13', 30),
(31, '2023-02-14', 31),
(32, '2023-02-15', 32),
(33, '2023-02-16', 33),
(34, '2023-02-17', 34),
(35, '2023-02-18', 35),
(36, '2023-02-19', 36),
(37, '2023-02-20', 37),
(38, '2023-02-21', 38),
(39, '2023-02-22', 39),
(40, '2023-02-23', 40),
(41, '2023-02-24', 41),
(42, '2023-02-25', 42);

-- Creating OrderDetails table
CREATE TABLE OrderDetails (
    OrderDetailID INTEGER NOT NULL PRIMARY KEY,
    OrderID INTEGER NOT NULL REFERENCES Orders(OrderID),
    ProductID INTEGER NOT NULL REFERENCES Products(ProductID),
    Quantity INTEGER NOT NULL
);

-- Insert sample data into OrderDetails table
INSERT INTO OrderDetails (OrderDetailID, OrderID, ProductID, Quantity) VALUES
(1, 1, 1, 1),
(2, 1, 10, 2),
(3, 2, 2, 1),
(4, 2, 12, 1),
(5, 3, 3, 1),
(6, 3, 16, 1),
(7, 4, 4, 1),
(8, 4, 17, 1),
(9, 5, 5, 1),
(10, 5, 20, 1),
(11, 6, 6, 1),
(12, 6, 31, 1),
(13, 7, 7, 1),
(14, 7, 35, 1),
(15, 8, 8, 1),
(16, 8, 33, 1),
(17, 9, 9, 1),
(18, 9, 18, 1),
(19, 10, 10, 1),
(20, 10, 40, 1),
(21, 11, 11, 1),
(22, 11, 30, 1),
(23, 12, 12, 1),
(24, 12, 14, 1),
(25, 13, 13, 1),
(26, 13, 15, 1),
(27, 14, 14, 1),
(28, 14, 21, 1),
(29, 15, 15, 1),
(30, 15, 23, 1),
(31, 16, 16, 1),
(32, 16, 24, 1),
(33, 17, 17, 1),
(34, 17, 29, 1),
(35, 18, 18, 1),
(36, 18, 34, 1),
(37, 19, 19, 1),
(38, 19, 36, 1),
(39, 20, 20, 1),
(40, 20, 28, 1),
(41, 21, 21, 1),
(42, 21, 25, 1),
(43, 22, 22, 1),
(44, 22, 26, 1),
(45, 23, 23, 1),
(46, 23, 41, 1),
(47, 24, 24, 1),
(48, 24, 19, 1),
(49, 25, 25, 1),
(50, 25, 38, 1),
(51, 26, 26, 1),
(52, 26, 32, 1),
(53, 27, 27, 1),
(54, 27, 42, 1),
(55, 28, 28, 1),
(56, 28, 39, 1),
(57, 29, 29, 1),
(58, 29, 11, 1),
(59, 30, 30, 1),
(60, 30, 6, 1),
(61, 31, 31, 1),
(62, 31, 22, 1),
(63, 32, 32, 1),
(64, 32, 5, 1),
(65, 33, 33, 1),
(66, 33, 9, 1),
(67, 34, 34, 1),
(68, 34, 7, 1),
(69, 35, 35, 1),
(70, 35, 8, 1),
(71, 36, 36, 1),
(72, 36, 27, 1),
(73, 37, 37, 1),
(74, 37, 4, 1),
(75, 38, 38, 1),
(76, 38, 3, 1),
(77, 39, 39, 1),
(78, 39, 2, 1),
(79, 40, 40, 1),
(80, 40, 13, 1),
(81, 41, 41, 1),
(82, 41, 37, 1),
(83, 42, 42, 1),
(84, 42, 20, 1);

-- Creating Reviews table
CREATE TABLE Reviews (
    ReviewID INTEGER NOT NULL PRIMARY KEY,
    UserID INTEGER NOT NULL REFERENCES Users(UserID),
    ProductID INTEGER NOT NULL REFERENCES Products(ProductID),
    Rating INTEGER NOT NULL CHECK (Rating >= 1 AND Rating <= 5),
    ReviewText VARCHAR(1000),
    ReviewDate DATE NOT NULL
);

-- Insert sample data into Reviews table
INSERT INTO Reviews (ReviewID, UserID, ProductID, Rating, ReviewText, ReviewDate) VALUES
-- Reviews for ProductID 1: MacBook Air M1
(1, 1, 1, 5, 'Absolutely love the MacBook Air M1! Super fast and lightweight.', '2023-02-15'),
(2, 2, 1, 4, 'Great performance but could use more ports.', '2023-03-16'),
(3, 3, 1, 5, 'Battery life is amazing on the M1 MacBook Air.', '2023-04-17'),
-- Reviews for ProductID 2: MacBook Pro M2
(4, 4, 2, 5, 'MacBook Pro M2 is a beast! Handles all my tasks smoothly.', '2023-05-18'),
(5, 5, 2, 4, 'Excellent laptop but a bit heavy.', '2023-06-19'),
(6, 6, 2, 5, 'The M2 chip is a significant improvement.', '2023-07-20'),
-- Reviews for ProductID 3: MacBook Pro M3
(7, 7, 3, 4, 'MacBook Pro M3 is powerful but expensive.', '2023-08-21'),
(8, 8, 3, 5, 'Best laptop for professionals.', '2023-09-22'),
(9, 9, 3, 4, 'Great performance but wish it had better battery life.', '2023-10-23'),
-- Reviews for ProductID 4: MacBook Pro M4
(10, 10, 4, 5, 'MacBook Pro M4 is the future of laptops.', '2023-11-24'),
(11, 11, 4, 5, 'Incredible speed and display.', '2023-12-25'),
(12, 12, 4, 4, 'Excellent but very pricey.', '2024-01-26'),
-- Reviews for ProductID 5: Apple Vision Pro
(13, 13, 5, 3, 'Apple Vision Pro is innovative but too expensive.', '2024-02-27'),
(14, 14, 5, 4, 'Amazing technology but not practical yet.', '2024-03-28'),
(15, 15, 5, 5, 'Blew my mind! The future is here.', '2024-04-29'),
-- Reviews for ProductID 6: Nvidia RTX 3080
(16, 16, 6, 4, 'Nvidia RTX 3080 delivers great performance for gaming.', '2023-03-16'),
(17, 17, 6, 5, 'Best value for high-end gaming.', '2023-04-17'),
(18, 18, 6, 4, 'Runs hot but performs exceptionally.', '2023-05-18'),
-- Reviews for ProductID 7: Nvidia RTX 3090
(19, 19, 7, 5, 'Unmatched performance for 4K gaming.', '2023-06-19'),
(20, 20, 7, 4, 'Very expensive but worth it for enthusiasts.', '2023-07-20'),
(21, 21, 7, 5, 'An absolute powerhouse!', '2023-08-21'),
-- Reviews for ProductID 8: Nvidia RTX 4080
(22, 22, 8, 4, 'Great performance but overpriced.', '2023-09-22'),
(23, 23, 8, 5, 'Handles all modern games at max settings.', '2023-10-23'),
(24, 24, 8, 4, 'Solid card but availability is an issue.', '2023-11-24'),
-- Reviews for ProductID 9: Nvidia RTX 4090
(25, 25, 9, 5, 'The best graphics card money can buy.', '2023-12-25'),
(26, 26, 9, 5, 'Ultimate performance for professional workloads.', '2024-01-26'),
(27, 27, 9, 4, 'Incredible but consumes a lot of power.', '2024-02-27'),
-- Reviews for ProductID 10: Samsung 980 Pro SSD
(28, 28, 10, 4, 'Samsung SSD is fast but a bit pricey.', '2023-06-19'),
(29, 29, 10, 5, 'Excellent speed for gaming and productivity.', '2023-07-20'),
(30, 30, 10, 5, 'Easy to install and blazing fast.', '2023-08-21'),
-- Reviews for ProductID 11: WD Black SN850 SSD
(31, 31, 11, 5, 'Top-notch SSD performance.', '2023-09-22'),
(32, 32, 11, 4, 'Great speeds but gets warm under load.', '2023-10-23'),
(33, 33, 11, 5, 'Best SSD I have ever used.', '2023-11-24'),
-- Reviews for ProductID 12: Cyberpunk 2077 (PC)
(34, 34, 12, 5, 'Cyberpunk 2077 has improved a lot since launch.', '2023-05-18'),
(35, 35, 12, 4, 'Great storyline but still some bugs.', '2023-06-19'),
(36, 36, 12, 5, 'Immersive world and characters.', '2023-07-20'),
-- Reviews for ProductID 13: Call of Duty: Modern Warfare II (PC)
(37, 37, 13, 4, 'Solid gameplay but maps could be better.', '2023-08-21'),
(38, 38, 13, 5, 'Best COD in years!', '2023-09-22'),
(39, 39, 13, 4, 'Multiplayer is very engaging.', '2023-10-23'),
-- Reviews for ProductID 14: PlayStation 5
(40, 40, 14, 5, 'PlayStation 5 offers great exclusive games.', '2023-08-21'),
(41, 41, 14, 5, 'Fast loading times and amazing graphics.', '2023-09-22'),
(42, 42, 14, 4, 'Controller is innovative but battery life is short.', '2023-10-23'),
-- Reviews for ProductID 15: Xbox Series X
(43, 1, 15, 5, 'Xbox Series X is a powerhouse console.', '2023-11-24'),
(44, 2, 15, 4, 'Game Pass makes it a great value.', '2023-12-25'),
(45, 3, 15, 5, 'Quick Resume feature is a game-changer.', '2024-01-26'),
-- Reviews for ProductID 16: Dell UltraSharp Monitor
(46, 4, 16, 5, 'Crystal clear display with vibrant colors.', '2024-02-27'),
(47, 5, 16, 4, 'Excellent monitor for photo editing.', '2024-03-28'),
(48, 6, 16, 5, 'Adjustable stand is very convenient.', '2024-04-29'),
-- Reviews for ProductID 17: Logitech MX Master 3 Mouse
(49, 7, 17, 5, 'Logitech MX Master 3 is the best mouse I"ve used.', '2023-09-22'),
(50, 8, 17, 5, 'Ergonomic and feature-packed.', '2023-10-23'),
(51, 9, 17, 4, 'Battery life could be better.', '2023-11-24'),
-- Reviews for ProductID 18: Razer Huntsman Elite Keyboard
(52, 10, 18, 5, 'Fantastic mechanical keyboard with great feedback.', '2023-12-25'),
(53, 11, 18, 4, 'RGB lighting is impressive.', '2024-01-26'),
(54, 12, 18, 5, 'Highly responsive keys.', '2024-02-27'),
-- Reviews for ProductID 19: Bose QC 35 II Headphones
(55, 13, 19, 5, 'Bose headphones have excellent noise cancellation.', '2024-04-29'),
(56, 14, 19, 5, 'Comfortable for long periods.', '2024-05-30'),
(57, 15, 19, 4, 'Sound quality is top-notch.', '2024-06-01'),
-- Reviews for ProductID 20: Samsung Galaxy S21 Ultra
(58, 16, 20, 5, 'Galaxy S21 Ultra is an amazing phone.', '2023-07-20'),
(59, 17, 20, 4, 'Camera is outstanding.', '2023-08-21'),
(60, 18, 20, 5, 'Display is vibrant and smooth.', '2023-09-22'),
-- Reviews for ProductID 21: iPhone 13 Pro Max
(61, 19, 21, 5, 'Best iPhone to date!', '2023-10-23'),
(62, 20, 21, 5, 'Battery life has improved significantly.', '2023-11-24'),
(63, 21, 21, 4, 'Pricey but worth it.', '2023-12-25'),
-- Reviews for ProductID 22: Google Pixel 6 Pro
(64, 22, 22, 5, 'Google Pixel 6 Pro has a fantastic camera.', '2024-06-01'),
(65, 23, 22, 4, 'Pure Android experience is great.', '2024-07-02'),
(66, 24, 22, 5, 'Excellent value for the features.', '2024-08-03'),
-- Reviews for ProductID 23: Amazon Echo Dot
(67, 25, 23, 4, 'Echo Dot is a handy smart home device.', '2023-09-22'),
(68, 26, 23, 5, 'Great for controlling smart devices.', '2023-10-23'),
(69, 27, 23, 4, 'Sound quality is decent for its size.', '2023-11-24'),
-- Reviews for ProductID 24: Philips Hue Smart Bulb
(70, 28, 24, 5, 'Smart bulbs are fun and easy to use.', '2023-12-25'),
(71, 29, 24, 4, 'A bit expensive but works well.', '2024-01-26'),
(72, 30, 24, 5, 'Love the color options.', '2024-02-27'),
-- Reviews for ProductID 25: Ring Video Doorbell Pro
(73, 31, 25, 4, 'Ring Doorbell adds security to my home.', '2024-05-30'),
(74, 32, 25, 5, 'Easy to install and use.', '2024-06-01'),
(75, 33, 25, 4, 'Subscription fee is a downside.', '2024-07-02'),
-- Reviews for ProductID 26: Fitbit Charge 5
(76, 34, 26, 5, 'Great fitness tracker with accurate measurements.', '2024-08-03'),
(77, 35, 26, 4, 'Display is bright and clear.', '2024-09-04'),
(78, 36, 26, 5, 'Battery life lasts a full week.', '2024-10-05'),
-- Reviews for ProductID 27: Apple Watch Series 7
(79, 37, 27, 4, 'Apple Watch Series 7 is a great fitness tracker.', '2023-10-23'),
(80, 38, 27, 5, 'New features are a welcome addition.', '2023-11-24'),
(81, 39, 27, 5, 'Integration with iPhone is seamless.', '2023-12-25'),
-- Reviews for ProductID 28: Microsoft Office 365 Subscription
(82, 40, 28, 3, 'Office 365 is a bit costly for personal use.', '2024-07-02'),
(83, 41, 28, 4, 'Useful for work but prefer one-time purchase.', '2024-08-03'),
(84, 42, 28, 5, 'Always updated with the latest features.', '2024-09-04'),
-- Reviews for ProductID 29: Adobe Photoshop CC Subscription
(85, 1, 29, 4, 'Photoshop CC is powerful but expensive.', '2024-01-26'),
(86, 2, 29, 5, 'Industry standard for image editing.', '2024-02-27'),
(87, 3, 29, 4, 'Steep learning curve but worth it.', '2024-03-28'),
-- Reviews for ProductID 30: Anker PowerCore Power Bank
(88, 4, 30, 5, 'Anker Power Bank is reliable and charges quickly.', '2023-09-22'),
(89, 5, 30, 5, 'Essential for travel.', '2023-10-23'),
(90, 6, 30, 4, 'A bit heavy but holds a lot of charge.', '2023-11-24'),
-- Reviews for ProductID 31: Seagate 4TB External Hard Drive
(91, 7, 31, 4, 'Seagate External Hard Drive offers ample storage.', '2024-08-03'),
(92, 8, 31, 5, 'Good value for the price.', '2024-09-04'),
(93, 9, 31, 4, 'Transfer speeds are decent.', '2024-10-05'),
-- Reviews for ProductID 32: NETGEAR Nighthawk WiFi 6 Router
(94, 10, 32, 5, 'Amazing router with excellent coverage.', '2023-12-25'),
(95, 11, 32, 4, 'Setup was a bit complicated.', '2024-01-26'),
(96, 12, 32, 5, 'Handles multiple devices smoothly.', '2024-02-27'),
-- Reviews for ProductID 33: Oculus Quest 2 VR Headset
(97, 13, 33, 5, 'Oculus Quest 2 provides an excellent VR experience.', '2023-11-24'),
(98, 14, 33, 5, 'Wireless VR is so convenient.', '2023-12-25'),
(99, 15, 33, 4, 'Wish it had more storage.', '2024-01-26'),
-- Reviews for ProductID 34: Norton 360 Deluxe
(100, 16, 34, 4, 'Solid security software.', '2024-03-28'),
(101, 17, 34, 5, 'Protects all my devices.', '2024-04-29'),
(102, 18, 34, 4, 'Occasionally slows down my PC.', '2024-05-30'),
-- Reviews for ProductID 35: Kaspersky Total Security
(103, 19, 35, 5, 'Comprehensive protection suite.', '2024-06-01'),
(104, 20, 35, 4, 'User-friendly interface.', '2024-07-02'),
(105, 21, 35, 5, 'Great value for the features.', '2024-08-03'),
-- Reviews for ProductID 36: Nintendo Switch
(106, 22, 36, 5, 'Nintendo Switch is fun for the whole family.', '2024-09-04'),
(107, 23, 36, 5, 'Love the portability.', '2024-10-05'),
(108, 24, 36, 4, 'Wish battery life was longer.', '2024-11-06'),
-- Reviews for ProductID 37: Asus ROG Gaming Laptop
(109, 25, 37, 5, 'Handles all games at high settings.', '2024-04-29'),
(110, 26, 37, 4, 'Runs a bit hot under load.', '2024-05-30'),
(111, 27, 37, 5, 'Excellent build quality.', '2024-06-01'),
-- Reviews for ProductID 38: Alienware Aurora Desktop
(112, 28, 38, 5, 'Alienware Desktop handles all my games with ease.', '2024-02-27'),
(113, 29, 38, 5, 'Upgradable and powerful.', '2024-03-28'),
(114, 30, 38, 4, 'Expensive but worth it.', '2024-04-29'),
-- Reviews for ProductID 39: HP Envy 13 Laptop
(115, 31, 39, 4, 'Sleek design and good performance.', '2023-11-24'),
(116, 32, 39, 5, 'Lightweight and portable.', '2023-12-25'),
(117, 33, 39, 4, 'Battery life could be better.', '2024-01-26'),
-- Reviews for ProductID 40: Logitech C920 HD Pro Webcam
(118, 34, 40, 4, 'Logitech Webcam is good for video conferencing.', '2024-03-28'),
(119, 35, 40, 5, 'Clear picture and easy setup.', '2024-04-29'),
(120, 36, 40, 5, 'Best webcam in this price range.', '2024-05-30'),
-- Reviews for ProductID 41: Canon EOS Rebel T7 DSLR Camera
(121, 37, 41, 4, 'Canon DSLR takes great photos for beginners.', '2023-12-25'),
(122, 38, 41, 5, 'Easy to use with excellent image quality.', '2024-01-26'),
(123, 39, 41, 4, 'Affordable entry-level DSLR.', '2024-02-27'),
-- Reviews for ProductID 42: JBL Flip 5 Bluetooth Speaker
(124, 40, 42, 5, 'Great sound quality for its size.', '2024-06-01'),
(125, 41, 42, 4, 'Portable and durable.', '2024-07-02'),
(126, 42, 42, 5, 'Battery life lasts all day.', '2024-08-03');
