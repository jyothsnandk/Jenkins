## CI/CD Deployment Assignment – Flask + Express on AWS EC2 with Jenkins

This project is a complete example for your assignment:

- **Flask backend** (`flask-app`) running on **port 5000**
- **Express frontend** (`express-app`) running on **port 3000**
- **Jenkins pipelines** (one `Jenkinsfile` in each repo) that:
  - Pull latest code from Git
  - Install dependencies
  - Restart the apps via **pm2** on an EC2 instance

You can split `flask-app` and `express-app` into **two separate GitHub repositories** to match the assignment requirement.

---

## 1. Project Structure (Local)

- **`flask-app/`**
  - `app.py` – simple Flask backend
  - `requirements.txt` – Python dependencies
  - `Jenkinsfile` – CI/CD pipeline for Flask
- **`express-app/`**
  - `server.js` – simple Express app
  - `package.json` – Node.js dependencies and start script
  - `Jenkinsfile` – CI/CD pipeline for Express

You will create two GitHub repos, for example:

- `https://github.com/<your-username>/flask-app`
- `https://github.com/<your-username>/express-app`

---

## 2. EC2 Setup (Part 1 – Manual Deployment)

### 2.1 Launch EC2 Instance

- **AMI**: Ubuntu Server 22.04 LTS (free tier)
- **Instance type**: `t2.micro` (or other free-tier)
- **Security group**:
  - **Allow inbound**:
    - SSH: TCP 22 (your IP)
    - HTTP: TCP 80 (0.0.0.0/0)
    - Custom TCP: 3000 and 5000 (0.0.0.0/0) – for testing

### 2.2 SSH into EC2

On your Windows machine (PowerShell or Git Bash):

```bash
ssh -i path/to/your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

### 2.3 Install System Dependencies

On the EC2 instance:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2
```

Verify:

```bash
python3 --version
pip3 --version
node -v
npm -v
pm2 -v
```

### 2.4 Clone the Applications

Assuming each app has its **own GitHub repo**:

```bash
cd ~
git clone https://github.com/<your-username>/flask-app.git
git clone https://github.com/<your-username>/express-app.git
```

### 2.5 Setup Flask App (Port 5000)

```bash
cd ~/flask-app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Run once to test:

```bash
python app.py
```

Open in browser:

- `http://<EC2_PUBLIC_IP>:5000/`

Stop with `Ctrl + C`, then run with **pm2**:

```bash
cd ~/flask-app
source venv/bin/activate
pm2 start "gunicorn -b 0.0.0.0:5000 app:app" --name flask-app
pm2 save
pm2 status
```

### 2.6 Setup Express App (Port 3000)

```bash
cd ~/express-app
npm install
```

Run once to test:

```bash
npm start
```

Open in browser:

- `http://<EC2_PUBLIC_IP>:3000/`

Stop with `Ctrl + C`, then run with **pm2**:

```bash
cd ~/express-app
pm2 start "npm start" --name express-app
pm2 save
pm2 status
```

Now both apps are running on the same EC2 instance:

- Flask: `http://<EC2_PUBLIC_IP>:5000/`
- Express: `http://<EC2_PUBLIC_IP>:3000/`

### 2.7 Architecture Description

- **Single EC2 instance** running:
  - **Flask** backend on port 5000 (managed by pm2 via gunicorn)
  - **Express** frontend on port 3000 (managed by pm2)
  - **Jenkins** (later, on port 8080)
- **GitHub** hosts two repositories.
- **Jenkins** pulls the code from GitHub and deploys to the same EC2 instance by restarting pm2 processes.

You can draw a simple diagram showing:

1. Developer pushes to GitHub.
2. GitHub webhook triggers Jenkins on EC2.
3. Jenkins pulls latest code, installs deps, restarts `flask-app` and `express-app` via pm2.
4. Users access EC2 public IP on ports 3000 and 5000.

---

## 3. Install Jenkins on the EC2 Instance

### 3.1 Install Java and Jenkins

```bash
sudo apt update
sudo apt install -y fontconfig openjdk-17-jre

curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

sudo apt update
sudo apt install -y jenkins
sudo systemctl enable jenkins
sudo systemctl start jenkins
sudo systemctl status jenkins
```

Open port **8080** in your EC2 security group (Custom TCP 8080, 0.0.0.0/0).

Then open in browser:

- `http://<EC2_PUBLIC_IP>:8080/`

### 3.2 Initial Jenkins Setup

- Get admin password:

```bash
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

- Paste into Jenkins UI.
- Install **suggested plugins**.
- Create **admin user** and finish setup.

### 3.3 Install Required Jenkins Plugins

In Jenkins UI:

- **Manage Jenkins → Plugins → Available**:
  - Install:
    - **Git plugin**
    - **Pipeline** (if not already)
    - Optionally **NodeJS** and **Python** plugins (not strictly required because we’re using system `node`/`python`).

Restart Jenkins if prompted.

---

## 4. Jenkins Pipelines (Part 2 – CI/CD)

You will create **two pipeline jobs** in Jenkins, each using the `Jenkinsfile` from the respective repo.

### 4.1 Flask Pipeline (`flask-app/Jenkinsfile`)

The `flask-app/Jenkinsfile` is already created and looks like this:

```groovy
pipeline {
    agent any

    environment {
        VENV_DIR = "venv"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Set up Python') {
            steps {
                sh 'python3 -m venv ${VENV_DIR} || python -m venv ${VENV_DIR}'
                sh '. ${VENV_DIR}/bin/activate && pip install --upgrade pip'
            }
        }

        stage('Install dependencies') {
            steps {
                sh '. ${VENV_DIR}/bin/activate && pip install -r requirements.txt'
            }
        }

        stage('Restart Flask app (pm2)') {
            steps {
                sh 'pm2 start "gunicorn -b 0.0.0.0:5000 app:app" --name flask-app || pm2 restart flask-app'
                sh 'pm2 save'
            }
        }
    }
}
```

### 4.2 Express Pipeline (`express-app/Jenkinsfile`)

The `express-app/Jenkinsfile` is already created and looks like this:

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Set up Node') {
            steps {
                sh 'node -v && npm -v'
            }
        }

        stage('Install dependencies') {
            steps {
                sh 'npm install'
            }
        }

        stage('Restart Express app (pm2)') {
            steps {
                sh 'pm2 start "npm start" --name express-app || pm2 restart express-app'
                sh 'pm2 save'
            }
        }
    }
}
```

### 4.3 Create Jenkins Pipeline Jobs

For **Flask app**:

- In Jenkins:
  - **New Item → Name**: `flask-app-pipeline`
  - Select **Pipeline**, click OK.
  - In **Pipeline** section:
    - Definition: **Pipeline script from SCM**
    - SCM: **Git**
    - Repository URL: `https://github.com/<your-username>/flask-app.git`
    - Branch: `*/main` (or `*/master`, depending on your repo)
    - Script Path: `Jenkinsfile`
  - Save.

For **Express app**:

- Repeat above steps with:
  - Name: `express-app-pipeline`
  - Repository URL: `https://github.com/<your-username>/express-app.git`

### 4.4 Add GitHub Webhooks (Trigger on Push)

In each GitHub repo (`flask-app`, `express-app`):

- Go to **Settings → Webhooks → Add webhook**
  - **Payload URL**: `http://<EC2_PUBLIC_IP>:8080/github-webhook/`
  - **Content type**: `application/json`
  - **Secret**: (optional, if used, configure same in Jenkins)
  - **Which events?**: “Just the push event”
  - Click **Add webhook**

In Jenkins, for each pipeline job:

- Go to job **Configure → Build Triggers**:
  - Check **GitHub hook trigger for GITScm polling**
  - Save.

Now, every `git push` to GitHub triggers the respective Jenkins pipeline.

---

## 5. Optional Enhancements

### 5.1 Add Testing Stages

**Flask** (example):

```groovy
stage('Test') {
    steps {
        sh '. ${VENV_DIR}/bin/activate && pytest || echo "No tests yet"'
    }
}
```

**Express** (example):

```groovy
stage('Test') {
    steps {
        sh 'npm test || echo "No tests yet"'
    }
}
```

### 5.2 Environment Variables / Secrets in Jenkins

- In Jenkins job configuration:
  - **Build Environment → Use secret text(s) or file(s)** or
  - **This project is parameterized** – add **String parameters**.
- Or globally in:
  - **Manage Jenkins → Credentials** – store API keys, DB passwords.
- Refer to them in `Jenkinsfile` via `environment` block, e.g.:

```groovy
environment {
    API_KEY = credentials('my-api-key-id')
}
```

---

## 6. What to Submit for Your Assignment

- **GitHub repository links**:
  - `flask-app` repo URL
  - `express-app` repo URL
- **This README** (possibly slightly edited with your screenshots/URLs).
- **Screenshots**:
  - Browser showing:
    - `http://<EC2_PUBLIC_IP>:5000/` (Flask response)
    - `http://<EC2_PUBLIC_IP>:3000/` (Express response)
  - Jenkins:
    - Dashboard with `flask-app-pipeline` and `express-app-pipeline`
    - Pipeline build page showing **Stages** all in green and logs where:
      - Code is pulled from Git
      - Dependencies are installed
      - pm2 restart commands run successfully

This repository and guide give you everything needed to implement and **demonstrate a working CI/CD deployment** of Flask and Express on a single EC2 instance using Jenkins. Adjust names, URLs, and ports as required by your instructions or college template.

Webhook test at Fri Jan 30 06:36:09 UTC 2026
