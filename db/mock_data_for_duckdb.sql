-- DuckDB SQL Script to Create Tables and Insert Data

-- Creating Users table
CREATE TABLE Users (
    UserID INTEGER NOT NULL PRIMARY KEY,
    FirstName VARCHAR(100) NOT NULL,
    LastName VARCHAR(100) NOT NULL,
    Email VARCHAR(255) NOT NULL UNIQUE
);

-- Insert sample data into Users table
INSERT INTO Users (UserID, FirstName, LastName, Email) VALUES
(1, 'John', 'Doe', 'john.doe@example.com'),
(2, 'Jane', 'Roe', 'jane.roe@example.com'),
(3, 'Alice', 'Smith', 'alice.smith@example.com'),
(4, 'Bob', 'Johnson', 'bob.johnson@example.com'),
(5, 'Carol', 'Williams', 'carol.williams@example.com'),
(6, 'David', 'Brown', 'david.brown@example.com'),
(7, 'Eve', 'Davis', 'eve.davis@example.com'),
(8, 'Frank', 'Miller', 'frank.miller@example.com'),
(9, 'Grace', 'Wilson', 'grace.wilson@example.com'),
(10, 'Hank', 'Moore', 'hank.moore@example.com'),
(11, 'Ivy', 'Taylor', 'ivy.taylor@example.com'),
(12, 'Jack', 'Anderson', 'jack.anderson@example.com'),
(13, 'Karen', 'Thomas', 'karen.thomas@example.com'),
(14, 'Leo', 'Jackson', 'leo.jackson@example.com'),
(15, 'Mia', 'White', 'mia.white@example.com'),
(16, 'Nick', 'Harris', 'nick.harris@example.com'),
(17, 'Olivia', 'Martin', 'olivia.martin@example.com'),
(18, 'Paul', 'Thompson', 'paul.thompson@example.com'),
(19, 'Quincy', 'Garcia', 'quincy.garcia@example.com'),
(20, 'Rachel', 'Martinez', 'rachel.martinez@example.com'),
(21, 'Sam', 'Robinson', 'sam.robinson@example.com'),
(22, 'Tina', 'Clark', 'tina.clark@example.com');

-- Creating Products table
CREATE TABLE Products (
    ProductID INTEGER NOT NULL PRIMARY KEY,
    ProductName VARCHAR(255) NOT NULL,
    Price DECIMAL(10, 2) NOT NULL,
    CategoryID INTEGER
);

-- Insert sample data into Products table
INSERT INTO Products (ProductID, ProductName, Price, CategoryID) VALUES
(1, 'Phone', 699.99, 1),
(2, 'Laptop', 1299.99, 2),
(3, 'Tablet', 399.99, 1),
(4, 'Monitor', 199.99, 1),
(5, 'Keyboard', 49.99, 1),
(6, 'Mouse', 29.99, 1),
(7, 'Printer', 149.99, 1),
(8, 'Router', 89.99, 1),
(9, 'External Hard Drive', 119.99, 1),
(10, 'Webcam', 59.99, 1),
(11, 'Headphones', 79.99, 1),
(12, 'Smartwatch', 199.99, 1),
(13, 'Desk Lamp', 39.99, 1),
(14, 'USB-C Cable', 19.99, 1),
(15, 'Graphic Tablet', 249.99, 2),
(16, 'Gaming Chair', 299.99, 2),
(17, 'Office Chair', 149.99, 2),
(18, 'Standing Desk', 399.99, 2),
(19, 'Laptop Stand', 59.99, 2),
(20, 'Bluetooth Speaker', 99.99, 1),
(21, 'SSD Drive', 139.99, 1),
(22, 'Graphics Card', 499.99, 2);

-- Creating Categories table
CREATE TABLE Categories (
    CategoryID INTEGER NOT NULL PRIMARY KEY,
    CategoryName VARCHAR(255) NOT NULL
);

-- Insert sample data into Categories table
INSERT INTO Categories (CategoryID, CategoryName) VALUES
(1, 'Electronics'),
(2, 'Computers'),
(3, 'Accessories'),
(4, 'Furniture'),
(5, 'Audio'),
(6, 'Peripherals'),
(7, 'Networking'),
(8, 'Storage'),
(9, 'Wearables'),
(10, 'Office Supplies'),
(11, 'Gaming'),
(12, 'Mobile Devices'),
(13, 'Cables'),
(14, 'Displays'),
(15, 'Input Devices'),
(16, 'Power Devices'),
(17, 'Cooling Devices'),
(18, 'Security Devices'),
(19, 'Virtual Reality'),
(20, 'Health Tech'),
(21, 'Smart Home'),
(22, 'Software');

-- Creating Orders table
CREATE TABLE Orders (
    OrderID INTEGER NOT NULL PRIMARY KEY,
    OrderDate DATE NOT NULL,
    UserID INTEGER NOT NULL REFERENCES Users(UserID)
);

-- Insert sample data into Orders table
INSERT INTO Orders (OrderID, OrderDate, UserID) VALUES
(1, '2023-10-15', 1),
(2, '2023-10-16', 2),
(3, '2023-10-17', 3),
(4, '2023-10-18', 4),
(5, '2023-10-19', 5),
(6, '2023-10-20', 6),
(7, '2023-10-21', 7),
(8, '2023-10-22', 8),
(9, '2023-10-23', 9),
(10, '2023-10-24', 10),
(11, '2023-10-25', 11),
(12, '2023-10-26', 12),
(13, '2023-10-27', 13),
(14, '2023-10-28', 14),
(15, '2023-10-29', 15),
(16, '2023-10-30', 16),
(17, '2023-10-31', 17),
(18, '2023-11-01', 18),
(19, '2023-11-02', 19),
(20, '2023-11-03', 20),
(21, '2023-11-04', 21),
(22, '2023-11-05', 22);

-- Creating OrderDetails table
CREATE TABLE OrderDetails (
    OrderDetailID INTEGER NOT NULL PRIMARY KEY,
    OrderID INTEGER NOT NULL REFERENCES Orders(OrderID),
    ProductID INTEGER NOT NULL REFERENCES Products(ProductID),
    Quantity INTEGER NOT NULL
);

-- Insert sample data into OrderDetails table
INSERT INTO OrderDetails (OrderDetailID, OrderID, ProductID, Quantity) VALUES
(1, 1, 1, 2),
(2, 1, 2, 1),
(3, 2, 1, 1),
(4, 3, 3, 4),
(5, 4, 4, 2),
(6, 5, 5, 5),
(7, 6, 6, 3),
(8, 7, 7, 1),
(9, 8, 8, 2),
(10, 9, 9, 1),
(11, 10, 10, 2),
(12, 11, 11, 3),
(13, 12, 12, 1),
(14, 13, 13, 4),
(15, 14, 14, 2),
(16, 15, 15, 1),
(17, 16, 16, 1),
(18, 17, 17, 2),
(19, 18, 18, 1),
(20, 19, 19, 3),
(21, 20, 20, 2),
(22, 21, 21, 1),
(23, 22, 22, 1);