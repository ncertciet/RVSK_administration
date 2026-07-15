pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        DEPLOY_HOST = '10.249.160.101'
        DEPLOY_USER = 'nvsk-dev-user'
        APP_DIR = '/home/nvsk-dev-user/RVSK_administration'

        APP_NAME = 'rvsk_administration'
        TEST_CONTAINER = 'rvsk_administration_test'
        IMAGE_NAME = 'rvsk-administration'

        DEPLOY_BRANCH = 'dev_administration'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Display Build Information') {
            steps {
                sh '''
                    echo "========================================"
                    echo "RVSK Administration Deployment"
                    echo "========================================"
                    echo "Jenkins Build Number : ${BUILD_NUMBER}"
                    echo "Git Branch           : ${DEPLOY_BRANCH}"
                    echo "Deployment Host      : ${DEPLOY_HOST}"
                    echo "========================================"
                '''
            }
        }

        stage('Test SSH Connection') {
            steps {
                sh '''
                    ssh \
                      -o BatchMode=yes \
                      -o ConnectTimeout=10 \
                      ${DEPLOY_USER}@${DEPLOY_HOST} \
                      "hostname && whoami && docker --version"
                '''
            }
        }

        stage('Update Source Code') {
            steps {
                sh '''
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        cd /home/nvsk-dev-user/RVSK_administration

                        echo "Fetching latest source code..."
                        git fetch origin

                        echo "Switching to dev_administration..."
                        git checkout dev_administration

                        echo "Resetting to origin/dev_administration..."
                        git reset --hard origin/dev_administration

                        echo "Current commit:"
                        git log -1 --oneline
                    '
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        cd /home/nvsk-dev-user/RVSK_administration

                        COMMIT_ID=$(git rev-parse --short HEAD)

                        echo "Building Docker image..."
                        echo "Image: rvsk-administration:${COMMIT_ID}"

                        docker build \
                          -t rvsk-administration:${COMMIT_ID} \
                          -t rvsk-administration:latest \
                          .
                    '
                '''
            }
        }

        stage('Test New Docker Image') {
            steps {
                sh '''
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        cd /home/nvsk-dev-user/RVSK_administration

                        COMMIT_ID=$(git rev-parse --short HEAD)

                        echo "Removing previous test container..."
                        docker rm -f rvsk_administration_test 2>/dev/null || true

                        echo "Starting test container on port 8001..."

                        docker run -d \
                          --name rvsk_administration_test \
                          --env-file /home/nvsk-dev-user/RVSK_administration/.env \
                          -p 127.0.0.1:8001:8000 \
                          rvsk-administration:${COMMIT_ID}

                        echo "Waiting for application startup..."
                        sleep 10

                        echo "Testing application health..."

                        curl --fail \
                          --silent \
                          --show-error \
                          http://127.0.0.1:8001/health

                        echo ""
                        echo "New Docker image passed health check."

                        docker rm -f rvsk_administration_test
                    '
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        cd /home/nvsk-dev-user/RVSK_administration

                        COMMIT_ID=$(git rev-parse --short HEAD)

                        echo "Finding currently deployed image..."

                        CURRENT_IMAGE=$(docker inspect \
                          --format="{{.Config.Image}}" \
                          rvsk_administration 2>/dev/null || true)

                        echo "Current image: ${CURRENT_IMAGE}"
                        echo "New image: rvsk-administration:${COMMIT_ID}"

                        if [ -n "${CURRENT_IMAGE}" ]; then
                            echo "${CURRENT_IMAGE}" > /tmp/rvsk_administration_previous_image
                        fi

                        echo "Stopping existing container..."
                        docker rm -f rvsk_administration 2>/dev/null || true

                        echo "Starting new container..."

                        docker run -d \
                          --name rvsk_administration \
                          --restart unless-stopped \
                          --env-file /home/nvsk-dev-user/RVSK_administration/.env \
                          -p 8000:8000 \
                          rvsk-administration:${COMMIT_ID}

                        echo "Waiting for production application..."
                        sleep 10
                    '
                '''
            }
        }

        stage('Production Health Check') {
            steps {
                sh '''
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        echo "Checking production container..."

                        curl --fail \
                          --silent \
                          --show-error \
                          http://127.0.0.1:8000/health

                        echo ""
                        echo "Production health check successful."

                        docker ps \
                          --filter name=rvsk_administration
                    '
                '''
            }
        }

        stage('Verify Nginx Route') {
            steps {
                sh '''
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        echo "Checking Nginx administration route..."

                        curl --fail \
                          --silent \
                          --show-error \
                          http://127.0.0.1/administration/health

                        echo ""
                        echo "Nginx route verification successful."
                    '
                '''
            }
        }
    }

    post {

        success {
            echo '========================================'
            echo 'RVSK Administration deployment SUCCESS'
            echo '========================================'
        }

        failure {
            echo '========================================'
            echo 'RVSK Administration deployment FAILED'
            echo 'Check the failed Jenkins stage and logs.'
            echo '========================================'
        }

        always {
            echo "Pipeline completed: ${BUILD_TAG}"
        }
    }
}
