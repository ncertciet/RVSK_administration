pipeline {
    agent any

    options {
        // Jenkins normally performs an automatic checkout before the stages.
        // We disable it because we have our own explicit Checkout stage.
        skipDefaultCheckout(true)

        // Prevent two deployments from running at the same time.
        disableConcurrentBuilds()

        timestamps()

        // Keep only the latest 20 Jenkins builds.
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        // -------------------------------------------------
        // Deployment Server
        // -------------------------------------------------
        DEPLOY_HOST = '10.249.160.101'
        DEPLOY_USER = 'nvsk-dev-user'

        // -------------------------------------------------
        // Application
        // -------------------------------------------------
        APP_DIR = '/home/nvsk-dev-user/RVSK_administration'
        DEPLOY_BRANCH = 'dev_administration'

        // -------------------------------------------------
        // Docker
        // -------------------------------------------------
        APP_NAME = 'rvsk_administration'
        TEST_CONTAINER = 'rvsk_administration_test'
        IMAGE_NAME = 'rvsk-administration'

        // Keep the latest 5 commit-tagged Docker images.
        IMAGES_TO_KEEP = '5'
    }

    stages {

        // =================================================
        // 1. CHECKOUT
        // =================================================
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // =================================================
        // 2. DISPLAY BUILD INFORMATION
        // =================================================
        stage('Display Build Information') {
            steps {
                sh '''
                    echo "========================================"
                    echo "RVSK Administration Deployment"
                    echo "========================================"
                    echo "Jenkins Build Number : ${BUILD_NUMBER}"
                    echo "Git Branch           : ${DEPLOY_BRANCH}"
                    echo "Deployment Host      : ${DEPLOY_HOST}"
                    echo "Application          : ${APP_NAME}"
                    echo "========================================"
                '''
            }
        }

        // =================================================
        // 3. TEST SSH CONNECTION
        // =================================================
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

        // =================================================
        // 4. UPDATE SOURCE CODE ON DEPLOYMENT VM
        // =================================================
        stage('Update Source Code') {
            steps {
                sh '''
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        cd /home/nvsk-dev-user/RVSK_administration

                        echo "========================================"
                        echo "Fetching latest source code..."
                        echo "========================================"

                        git fetch origin

                        echo "Switching to dev_administration..."
                        git checkout dev_administration

                        echo "Resetting local repository to origin/dev_administration..."
                        git reset --hard origin/dev_administration

                        echo ""
                        echo "Current Git commit:"
                        git log -1 --oneline

                        echo ""
                        echo "Git status:"
                        git status --short
                    '
                '''
            }
        }

        // =================================================
        // 5. BUILD DOCKER IMAGE
        // =================================================
        stage('Build Docker Image') {
            steps {
                sh '''
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        cd /home/nvsk-dev-user/RVSK_administration

                        COMMIT_ID=$(git rev-parse --short HEAD)

                        echo "========================================"
                        echo "Building Docker Image"
                        echo "========================================"
                        echo "Image: rvsk-administration:${COMMIT_ID}"
                        echo "========================================"

                        docker build \
                          -t rvsk-administration:${COMMIT_ID} \
                          -t rvsk-administration:latest \
                          .

                        echo ""
                        echo "Docker image built successfully."

                        docker images rvsk-administration
                    '
                '''
            }
        }

        // =================================================
        // 6. TEST NEW IMAGE ON TEMPORARY PORT 8001
        // =================================================
        stage('Test New Docker Image') {
            steps {
                sh '''
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        cd /home/nvsk-dev-user/RVSK_administration

                        COMMIT_ID=$(git rev-parse --short HEAD)
                        TEST_CONTAINER="rvsk_administration_test"

                        echo "========================================"
                        echo "Testing New Docker Image"
                        echo "========================================"
                        echo "Image: rvsk-administration:${COMMIT_ID}"
                        echo "Temporary Port: 8001"
                        echo "========================================"

                        # Remove any previous test container.
                        docker rm -f "${TEST_CONTAINER}" 2>/dev/null || true

                        echo "Starting temporary test container..."

                        docker run -d \
                          --name "${TEST_CONTAINER}" \
                          --env-file /home/nvsk-dev-user/RVSK_administration/.env \
                          -p 127.0.0.1:8001:8000 \
                          rvsk-administration:${COMMIT_ID}

                        echo ""
                        echo "Waiting for application health check..."

                        HEALTH_OK=0

                        for i in 1 2 3 4 5 6; do

                            echo "Health check attempt ${i}/6..."

                            if curl \
                                --fail \
                                --silent \
                                --show-error \
                                http://127.0.0.1:8001/health
                            then
                                echo ""
                                echo "Test container is healthy."
                                HEALTH_OK=1
                                break
                            fi

                            sleep 5
                        done

                        if [ "${HEALTH_OK}" -ne 1 ]; then

                            echo ""
                            echo "ERROR: Test container failed health check."

                            echo ""
                            echo "Test container logs:"
                            docker logs "${TEST_CONTAINER}" || true

                            docker rm -f "${TEST_CONTAINER}" || true

                            exit 1
                        fi

                        echo ""
                        echo "New Docker image passed pre-deployment testing."

                        docker rm -f "${TEST_CONTAINER}"
                    '
                '''
            }
        }

        // =================================================
        // 7. DEPLOY WITH AUTOMATIC ROLLBACK
        // =================================================
        stage('Deploy with Automatic Rollback') {
            steps {
                sh '''
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        cd /home/nvsk-dev-user/RVSK_administration

                        COMMIT_ID=$(git rev-parse --short HEAD)

                        NEW_IMAGE="rvsk-administration:${COMMIT_ID}"
                        APP_CONTAINER="rvsk_administration"

                        echo "========================================"
                        echo "Production Deployment"
                        echo "========================================"
                        echo "New Image: ${NEW_IMAGE}"
                        echo "========================================"

                        # -----------------------------------------
                        # Find currently deployed image
                        # -----------------------------------------

                        CURRENT_IMAGE=$(docker inspect \
                          --format="{{.Config.Image}}" \
                          "${APP_CONTAINER}" \
                          2>/dev/null || true)

                        echo ""
                        echo "Current production image: ${CURRENT_IMAGE}"
                        echo "New production image    : ${NEW_IMAGE}"

                        # Save previous image information.
                        if [ -n "${CURRENT_IMAGE}" ]; then

                            echo "${CURRENT_IMAGE}" \
                              > /tmp/rvsk_administration_previous_image

                            echo "Rollback image saved:"
                            echo "${CURRENT_IMAGE}"

                        else

                            echo "No existing production container found."

                        fi

                        # -----------------------------------------
                        # Stop old production container
                        # -----------------------------------------

                        echo ""
                        echo "Stopping existing production container..."

                        docker rm -f "${APP_CONTAINER}" \
                          2>/dev/null || true

                        # -----------------------------------------
                        # Start new production container
                        # -----------------------------------------

                        echo ""
                        echo "Starting new production container..."

                        if ! docker run -d \
                          --name "${APP_CONTAINER}" \
                          --restart unless-stopped \
                          --env-file /home/nvsk-dev-user/RVSK_administration/.env \
                          -p 8000:8000 \
                          "${NEW_IMAGE}"
                        then
                            echo ""
                            echo "ERROR: Failed to start new production container."
                            DEPLOYMENT_FAILED=1
                        else
                            DEPLOYMENT_FAILED=0
                        fi

                        # -----------------------------------------
                        # Production health check
                        # -----------------------------------------

                        if [ "${DEPLOYMENT_FAILED}" -eq 0 ]; then

                            echo ""
                            echo "Waiting for production application..."

                            PRODUCTION_HEALTH_OK=0

                            for i in 1 2 3 4 5 6; do

                                echo "Production health check attempt ${i}/6..."

                                if curl \
                                    --fail \
                                    --silent \
                                    --show-error \
                                    http://127.0.0.1:8000/health
                                then
                                    echo ""
                                    echo "New production container is healthy."
                                    PRODUCTION_HEALTH_OK=1
                                    break
                                fi

                                sleep 5
                            done

                            if [ "${PRODUCTION_HEALTH_OK}" -ne 1 ]; then
                                DEPLOYMENT_FAILED=1
                            fi

                        fi

                        # -----------------------------------------
                        # Deployment successful
                        # -----------------------------------------

                        if [ "${DEPLOYMENT_FAILED}" -eq 0 ]; then

                            echo ""
                            echo "========================================"
                            echo "DEPLOYMENT SUCCESSFUL"
                            echo "========================================"
                            echo "Running image: ${NEW_IMAGE}"
                            echo "========================================"

                            docker ps \
                              --filter name="${APP_CONTAINER}"

                            exit 0

                        fi

                        # =========================================
                        # AUTOMATIC ROLLBACK
                        # =========================================

                        echo ""
                        echo "========================================"
                        echo "NEW DEPLOYMENT FAILED"
                        echo "STARTING AUTOMATIC ROLLBACK"
                        echo "========================================"

                        echo ""
                        echo "Failed container logs:"

                        docker logs \
                          --tail 100 \
                          "${APP_CONTAINER}" \
                          2>/dev/null || true

                        echo ""
                        echo "Removing failed production container..."

                        docker rm -f "${APP_CONTAINER}" \
                          2>/dev/null || true

                        # -----------------------------------------
                        # Check previous image
                        # -----------------------------------------

                        if [ -z "${CURRENT_IMAGE}" ]; then

                            echo ""
                            echo "CRITICAL ERROR:"
                            echo "No previous Docker image is available for rollback."

                            exit 1

                        fi

                        echo ""
                        echo "Rolling back to:"
                        echo "${CURRENT_IMAGE}"

                        # -----------------------------------------
                        # Start previous image
                        # -----------------------------------------

                        if ! docker run -d \
                          --name "${APP_CONTAINER}" \
                          --restart unless-stopped \
                          --env-file /home/nvsk-dev-user/RVSK_administration/.env \
                          -p 8000:8000 \
                          "${CURRENT_IMAGE}"
                        then

                            echo ""
                            echo "CRITICAL ERROR:"
                            echo "Failed to start rollback container."

                            exit 1

                        fi

                        # -----------------------------------------
                        # Verify rollback
                        # -----------------------------------------

                        echo ""
                        echo "Verifying rollback deployment..."

                        ROLLBACK_HEALTH_OK=0

                        for i in 1 2 3 4 5 6; do

                            echo "Rollback health check attempt ${i}/6..."

                            if curl \
                                --fail \
                                --silent \
                                --show-error \
                                http://127.0.0.1:8000/health
                            then
                                echo ""
                                echo "Rollback container is healthy."
                                ROLLBACK_HEALTH_OK=1
                                break
                            fi

                            sleep 5
                        done

                        if [ "${ROLLBACK_HEALTH_OK}" -eq 1 ]; then

                            echo ""
                            echo "========================================"
                            echo "ROLLBACK SUCCESSFUL"
                            echo "========================================"
                            echo "Restored image: ${CURRENT_IMAGE}"
                            echo "========================================"

                        else

                            echo ""
                            echo "========================================"
                            echo "CRITICAL: ROLLBACK FAILED"
                            echo "========================================"

                            docker logs \
                              --tail 100 \
                              "${APP_CONTAINER}" \
                              2>/dev/null || true

                        fi

                        # Jenkins build must remain FAILED because
                        # the requested new version was not deployed.
                        exit 1
                    '
                '''
            }
        }

        // =================================================
        // 8. VERIFY NGINX ROUTE
        // =================================================
        stage('Verify Nginx Route') {
            steps {
                sh '''
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        echo "========================================"
                        echo "Checking Nginx Administration Route"
                        echo "========================================"

                        HEALTH_OK=0

                        for i in 1 2 3 4 5; do

                            echo "Nginx health check attempt ${i}/5..."

                            if curl \
                                --fail \
                                --silent \
                                --show-error \
                                http://127.0.0.1/administration/health
                            then
                                echo ""
                                echo "Nginx route verification successful."
                                HEALTH_OK=1
                                break
                            fi

                            sleep 3
                        done

                        if [ "${HEALTH_OK}" -ne 1 ]; then

                            echo ""
                            echo "ERROR: Nginx route verification failed."

                            exit 1

                        fi
                    '
                '''
            }
        }

        // =================================================
        // 9. DOCKER IMAGE CLEANUP
        // =================================================
        stage('Docker Image Cleanup') {
            steps {
                sh '''
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        IMAGE_NAME="rvsk-administration"
                        IMAGES_TO_KEEP=5

                        echo "========================================"
                        echo "Docker Image Cleanup"
                        echo "========================================"

                        echo ""
                        echo "Images before cleanup:"

                        docker images \
                          "${IMAGE_NAME}" \
                          --format "table {{.Repository}}\\t{{.Tag}}\\t{{.ID}}\\t{{.CreatedSince}}"

                        echo ""
                        echo "Currently running image:"

                        RUNNING_IMAGE=$(docker inspect \
                          --format="{{.Config.Image}}" \
                          rvsk_administration \
                          2>/dev/null || true)

                        echo "${RUNNING_IMAGE}"

                        echo ""
                        echo "Keeping the latest ${IMAGES_TO_KEEP} commit-tagged images."

                        # Get image references ordered newest first.
                        # Exclude the mutable latest tag.
                        OLD_IMAGES=$(docker images \
                          "${IMAGE_NAME}" \
                          --format "{{.Repository}}:{{.Tag}}" \
                          | grep -v ":latest$" \
                          | awk "!seen[\\$0]++" \
                          | tail -n +$((IMAGES_TO_KEEP + 1)) \
                          || true)

                        if [ -n "${OLD_IMAGES}" ]; then

                            echo ""
                            echo "Old images selected for cleanup:"
                            echo "${OLD_IMAGES}"

                            echo "${OLD_IMAGES}" | while read IMAGE; do

                                if [ -z "${IMAGE}" ]; then
                                    continue
                                fi

                                # Never remove the image currently used
                                # by the production container.
                                if [ "${IMAGE}" = "${RUNNING_IMAGE}" ]; then

                                    echo "Skipping running image: ${IMAGE}"

                                else

                                    echo "Removing old image: ${IMAGE}"

                                    docker image rm "${IMAGE}" \
                                      2>/dev/null || true

                                fi

                            done

                        else

                            echo ""
                            echo "No old application images need cleanup."

                        fi

                        echo ""
                        echo "Removing dangling Docker images..."

                        docker image prune -f

                        echo ""
                        echo "Images after cleanup:"

                        docker images \
                          "${IMAGE_NAME}" \
                          --format "table {{.Repository}}\\t{{.Tag}}\\t{{.ID}}\\t{{.CreatedSince}}"

                        echo ""
                        echo "Docker disk usage:"

                        docker system df
                    '
                '''
            }
        }
    }

    // =====================================================
    // POST ACTIONS
    // =====================================================
    post {

        success {
            echo '========================================'
            echo 'RVSK Administration deployment SUCCESS'
            echo '========================================'
            echo "Build: ${BUILD_NUMBER}"
            echo "Branch: ${DEPLOY_BRANCH}"
        }

        failure {
            echo '========================================'
            echo 'RVSK Administration deployment FAILED'
            echo '========================================'
            echo 'Check the failed Jenkins stage.'
            echo 'If deployment itself failed, the pipeline attempted automatic rollback.'
        }

        always {
            echo "Pipeline completed: ${BUILD_TAG}"
        }
    }
}
