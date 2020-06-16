pipeline {
    agent none
    stages {
        stage('Run linters') {
            agent {
                dockerfile {
                    filename 'Dockerfile.test'
                }
            }
            steps {
                parallel(
                    prospector: {
                        sh 'prospector --strictness=veryhigh --no-autodetect --ignore-paths=venv --max-line-length=200 .'
                    },
                    mypy: {
                        sh 'mypy --ignore-missing-imports --follow-imports=silent --show-column-numbers .'
                    }
                )
            }
        }
        stage('Build Docker image') {
            agent any
            steps {
                sh 'docker build -t docker-container-watchdog:$BUILD_NUMBER .'
            }
        }
        stage('Deploy Docker container') {
            agent any
            steps {
                sh 'docker stop container-watchdog'
                sh 'docker run --name container-watchdog --rm -d -v /var/run/docker.sock:/var/run/docker.sock --security-opt label=disable docker-container-watchdog:$BUILD_NUMBER'
            }
        }
    }
}
