pipeline {
  agent any


  environment {
    SERVICE_NAME = "free-games-notifier"
    /*  You need to create the folder first, and give Jenkins the correct permissions:
        sudo mkdir /opt/stacks/SERVICE_NAME
        sudo chown -R jenkins:jenkins /opt/stacks/SERVICE_NAME
        
        Ensure the docker-compose file is named "compose.yaml"
        
        All names and variables inside compose file should be consistent
    */
    DOCKGE_STACK_DIR = "/opt/stacks/$SERVICE_NAME"
  }

  stages {
    stage('Checkout') {
      steps {
        git branch: 'main', url: 'git@github.com:JulioMoralesB/' + SERVICE_NAME + '.git'
      }
    }

    stage('Build Docker Image') {
      steps {
        sh 'docker build -t $SERVICE_NAME:latest .'
      }
    }
    stage('Update Dockge Stack') {
      steps {
        sh '''
          # Copy compose.yaml to Dockge folder
          cp compose.yaml $DOCKGE_STACK_DIR/compose.yaml

          # Go to Dockge and restart stack
          cd $DOCKGE_STACK_DIR
          docker compose down
          docker compose up -d
        '''
      }
    }
    stage('Remove Dangling Images'){
            steps{
                script{
                    sh "docker images --quiet --filter=dangling=true | xargs --no-run-if-empty docker rmi || true"
                }
            }
        }
  }
}
