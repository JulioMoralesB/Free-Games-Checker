pipeline {
    agent any

    environment {
        IMAGE_NAME = "apollox10/free-games-checker"
    }

    stages {
        stage('Check Docker Version') {
            steps {
                script {
                    sh 'docker --version'
                    sh 'docker compose version'
                }
            }
        }
        stage('Checkout Code') {
            steps {
                git (
                    url: 'https://github.com/JulioMoralesB/Free-Games-Checker',
                    credentialsId: 'github-token',
                    branch: 'main'
                    )
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    
                    withCredentials([string(credentialsId: 'free-games-checker-webhook', variable: 'DISCORD_WEBHOOK_URL')
                                     ]) {
                        sh "docker compose -f docker-compose.yaml up -d --build"
                    }
                }
            }
        }
        stage('Remove Dangling Images'){
            steps{
                script{
                    sh "docker images --quiet --filter=dangling=true | xargs --no-run-if-empty docker rmi"
                }
            }
        }
    }

    post {
        success {
            echo "Deployment successful!"
            script {
                def webhookUrl = "${env.DISCORD_WEBHOOK_URL}"
                def payload = """{
                    "content": "Build successful for ${env.JOB_NAME} #${env.BUILD_NUMBER}. <${env.BUILD_URL}|View Build>"
                }"""
                httpRequest(
                    url: webhookUrl,
                    httpMode: 'POST',
                    contentType: 'APPLICATION_JSON',
                    requestBody: payload
                )
            }
        }
        failure {
            echo "Deployment failed!"
            script {
                def webhookUrl = "${env.DISCORD_ALERT_WEBHOOK_URL}"
                def payload = """{
                    "content": "Build failed for ${env.JOB_NAME} #${env.BUILD_NUMBER}. <${env.BUILD_URL}|View Build>"
                }"""
                httpRequest(
                    url: webhookUrl,
                    httpMode: 'POST',
                    contentType: 'APPLICATION_JSON',
                    requestBody: payload
                )
            }
        }
    }
}
