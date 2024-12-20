
# Finance Buddy

A personal finance management application built with Flask and Bootstrap, allowing users to manage income, expenses, and visualize financial data. 


## Tech Stack
* Backend: Flask Framework
* Frontend: HTML, CSS, Bootstrap
* Database: SQLite
* Authentication: Flask sessions
* Testing: unittest (Python) for backend tests


## Setup Instructions
### Prerequisites
* Python 3.10.0 installed
* SQLite 

## Features
**1. User Authentication:** 

* Secure Signup, Login, and Logout functionality.

![Screenshot 2024-12-19 232403](https://github.com/user-attachments/assets/84177556-4e31-4aeb-82cd-984c4bfda475)

![Screenshot 2024-12-19 231834](https://github.com/user-attachments/assets/611b1d95-4078-4f06-b4f6-64bca3643f79)


**2. Transaction Management:** 

* *__Add Transaction with OCR:__*
  
  User can add a transaction based on type: Expense or Income. This page also includes an option to upload the bill. We use *Python-tesseract* and Regex to extract the bill amount from the uploaded image and auto populate the amount field.

![Screenshot 2024-12-19 234523](https://github.com/user-attachments/assets/45ddc5ef-6d2c-413b-be4c-93734744ee19)

* *__View Transaction__*:
  
  User can view their monthly and as well as all time transaction history. Various filters are also available:

![Screenshot 2024-12-19 234945](https://github.com/user-attachments/assets/3c8d4478-a30e-43d7-8663-19ef376e4595)

![Screenshot 2024-12-19 235836](https://github.com/user-attachments/assets/bd28d323-e7c8-414e-a2fd-344e06e50515)

![Screenshot 2024-12-20 000035](https://github.com/user-attachments/assets/a7881748-1bf8-48c2-b429-5ebd6600c5c6)

* *__Edit and Delete Transaction__*:

![Screenshot 2024-12-20 000506](https://github.com/user-attachments/assets/5ef95c5e-1313-4121-a7e9-32cf0269201a)

![Screenshot 2024-12-20 000640](https://github.com/user-attachments/assets/42ca5e2d-9a92-44ae-8ee4-12872d0b4685)

**3. Dashboard and Statistics:** Visualize spending trends with charts.

* *__Dashboard:__*: At a glance view of the current month income and spending trends

  
![Screenshot 2024-12-20 062309](https://github.com/user-attachments/assets/ad32f213-9957-4537-94cb-44b51a4b260f)

* *__Statistics__*: Visual aid to review category wise income and expense both monthly and yearly

![Screenshot 2024-12-20 062610](https://github.com/user-attachments/assets/dc39a5dc-515d-4381-bfe2-7094678ef7c6)

![Screenshot 2024-12-20 062815](https://github.com/user-attachments/assets/c628f178-1e06-4a41-b890-2b3a6c13fd31)


