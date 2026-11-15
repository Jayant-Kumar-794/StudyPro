# StudyPro
StudyPro – Student Task &amp; Exam Manager


StudyPro is a Python-based desktop application designed to help students organize their academic activities, manage assignments, track examinations, and monitor upcoming deadlines in one place.

Built using Python Tkinter for the graphical user interface and SQLite for data storage, StudyPro provides a convenient environment for students to manage their academic schedules and monitor their progress.

The application offers a centralized dashboard where students can manage their tasks, organize academic activities, and keep track of their study progress.

1. Project Overview

Managing multiple assignments, class tests, examinations, and academic deadlines can be challenging for students.

StudyPro aims to simplify this process by providing a desktop-based task management system that allows students to:

Organize assignments and class tests.

Track upcoming and overdue deadlines.

Monitor task completion status.

Manage academic activities from a single dashboard.

Maintain their academic task records using a local database.

StudyPro is designed to make academic planning more organized, accessible, and efficient.

2. Features

User Authentication

Student login.

New user registration.

User session management.

Task Management

Create and manage academic tasks.

Add assignments and class tests.

Provide task titles, descriptions, and subjects.

Set due dates.

Assign priority levels: Low, Medium, and High.

Update task progress.

Mark tasks as completed.

Dashboard

Centralized view of academic activities.

Overview of tasks and deadlines.

Monitor assignment and test progress.

Deadline Tracking

Identify upcoming deadlines.

Track overdue tasks.

Organize tasks according to their due dates.

User Interface

Modern desktop interface.

Styled widgets and customized themes.

Navigation between application screens.

Mouse-wheel scrolling support.

Dialog boxes, popups, and notifications.

Data Storage

SQLite database integration.

Persistent storage of application data.

Local database management.

3. Technologies Used

Technology

Purpose

Python

Core programming language

Tkinter

Desktop graphical user interface

ttk

Styled GUI components

SQLite

Database management

Pillow (if installed)

Image processing and graphics

Python OOP

Application structure and modular development

4. Project Structure

StudyPro/
│
├── main.py
│
├── app.py
│
├── studypro/
│   ├── app.py
│   ├── theme.py
│   ├── gfx.py
│   ├── models.py
│   │
│   ├── pages/
│   │   ├── auth.py
│   │   └── dashboard.py
│   │
│   ├── components/
│   │   └── task_card.py
│   │
│   └── widgets/
│
├── database/
│   ├── __init__.py
│   ├── db_connection.py
│   ├── seed.py
│   └── studypro.db
│
└── README.md

Note: This is an illustrative structure. Some modules and directories may contain additional files in the complete project.

5. System Requirements

Operating System: Windows / Linux / macOS

Python 3.8 or newer

Tkinter support

SQLite3

Required Python packages installed

6. Installation and Setup

Step 1: Download or Clone the Project

Download the project files or clone the repository.

git clone <repository-url>

Navigate to the project directory:

cd StudyPro

Step 2: Install Dependencies

Install the required external packages, if they are not already installed.

pip install pillow

If Tkinter is missing:

Windows: Reinstall Python from the official Python website and select the Tcl/Tk and IDLE option.

Linux:

sudo apt install python3-tk

Step 3: Run the Application

Execute the main Python file:

python main.py

On some systems, use:

python3 main.py

The application window will open.

7. User Instructions

A. Login

Launch the StudyPro application.

The login screen will appear if no user session is remembered.

Enter your registered email address.

Enter your password.

Click the Login button.

After successful authentication, you will be directed to the dashboard.

Demo Login Credentials

Email: aarav@student.edu

Password: study123

B. Register a New Account

Open the registration option.

Enter the required registration details.

Complete the registration process.

Use your registered credentials to log in.

C. Dashboard

After logging in, the dashboard provides access to your academic task management features.

Use the available navigation options to access the different sections of the application.

D. Add and Manage Tasks

Navigate to the task management section.

Select the option to add a task.

Enter the task title.

Provide a description.

Select the subject.

Choose the task type:

Assignment

Class Test

Select the due date.

Choose the priority:

Low

Medium

High

Save the task.

E. Update Task Status

Tasks can be organized according to their progress:

Not Started: Task has not yet been started.

In Progress: Work is currently being completed.

Completed: Task has been finished.

Update the status as you progress through your academic activities.

F. Track Deadlines

Use the dashboard and task information to monitor upcoming deadlines and identify overdue tasks.

Try to complete high-priority tasks before their due dates.

G. Exit the Application

Close the application window using the close button. The application handles database closure during shutdown.

8. Database

StudyPro uses SQLite to store application information locally.

The database is located at:

database/studypro.db

The application initializes its database on the first run and uses the database for persistent data storage.

To reset the demo database and restore its initial data, run:

python database/seed.py

Warning: Resetting demo data may remove previously stored application records. Back up important data before running the reset command.

9. Application Workflow

          Start Application
                 |
                 v
          Login / Register
                 |
                 v
             Dashboard
                 |
          +------+------+
          |      |      |
          v      v      v
        Tasks  Deadlines Progress
          |      |      |
          +------+------+
                 |
                 v
          Update Task Status
                 |
                 v
          Save Data in SQLite
                 |
                 v
             Exit

10. Key Advantages

Simple and user-friendly desktop application.

Centralized academic task management.

Organized assignment and test tracking.

Priority-based task organization.

Local database storage.

Modular Python application structure.

No browser required to use the desktop application.

11. Future Enhancements

The following features can be considered for future development:

Advanced academic performance analytics.

Pomodoro study timer.

Interactive academic calendar.

Enhanced deadline reminder system.

Productivity tracking and achievement badges.

Export academic task reports.

Backup and restore functionality.

12. Project Information

Project Name: StudyPro – Student Task & Exam Manager

Application Type: Desktop Application

Programming Language: Python

GUI Framework: Tkinter

Database: SQLite

Purpose: To help students organize, manage, and track their academic tasks and examination schedules efficiently.

StudyPro – Plan Better. Stay Organized. Achieve More.
