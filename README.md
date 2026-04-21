# 🌌 Cloud Cost Optimization Platform

This is a high-fidelity, Flask-based cloud optimization engine designed to analyze infrastructure usage, identify cost leaks, and provide actionable savings recommendations. Featuring a premium "Galaxy Edition" design system, it combines advanced data science with a professional UX.

![Project Dashboard](https://img.shields.io/badge/UI-Galaxy_Edition-blueviolet?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-3.0+-green?style=for-the-badge&logo=flask)
![Pandas](https://img.shields.io/badge/Pandas-2.2-blue?style=for-the-badge&logo=pandas)

---

## 🚀 Key Features

- **Cost Analysis Engine**: Upload infrastructure usage data (CSV) and let the system calculate costs and utilization metrics.
- **Rule-Based Recommendations**: Automatic detection of underutilized instances based on configurable threshold rules.
- **Advanced Analytics**: Interactive spending trends and breakdown visualizations powered by Chart.js.
- **Resource Management**: Dedicated area to track and manage cloud resources across different service types.
- **Dynamic Dashboard**: Real-time overview of the latest activities and infrastructure health.

## 🛠️ Technology Stack

- **Backend**: Python 3.13+, Flask
- **ORM & DB**: SQLAlchemy, SQLite
- **Data Engineering**: Pandas (for CSV parsing and cost calculation)
- **Frontend**: Vanilla HTML5, CSS3 (Custom "Galaxy" Design System), Bootstrap 5
- **Charts**: Chart.js

---

## 📋 Installation & Setup

### 1. Prerequisites
- Python 3.7 or higher installed.
- Git (for version control).

### 2. Clone the Repository
```bash
git clone https://github.com/y-kanchan/Cloud-Cost-Optimization-Platform.git
cd Cloud-Cost-Optimization-Platform
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```
The application will be accessible at `http://127.0.0.1:5000`.

---

## 📊 Usage Guide

1. **Register/Login**: Access your private optimization portal.
2. **Upload Data**: Navigate to 'Upload' and provide a CSV file with columns: `resource_name`, `resource_type`, `utilization_percent`, and `usage_hours`.
3. **Analyze**: View generated reports highlighting potential savings and specific optimization tasks.
4. **Resources**: Manually add or audit cloud resources in the resource management area.
5. **Analytics**: Monitor monthly spending trends and category breakdowns in the Analytics tab.

---

## 🌌 "Prism" Design System (Galaxy Edition)

The platform utilizes a custom-built design system characterized by:
- **Glassmorphism**: Translucent card effects with subtle backdrops.
- **Vibrant Gradients**: Deep purples, cosmic oranges, and galaxy blues.
- **Micro-animations**: Interactive elements that feel responsive and "alive."

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
*Created with ❤️ for Cloud Efficiency.*
