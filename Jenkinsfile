// Pipeline for building Bitcoin SV for QA use
pipeline {
    agent { 
        dockerfile  true
    }

    triggers {
        bitBucketTrigger([[$class: 'BitBucketPPRRepositoryTriggerFilter'
                   , actionFilter: [$class: 'BitBucketPPRRepositoryPushActionFilter'
                   , allowedBranches: 'Centos8'
                   , triggerAlsoIfTagPush: false]]
                   , [$class: 'BitBucketPPRPullRequestTriggerFilter'
                   , actionFilter: [$class: 'BitBucketPPRPullRequestApprovedActionFilter'
                   , triggerOnlyIfAllReviewersApproved: false]]])
    }

    stages {

        stage ('Build') {
            steps {
                bitbucketStatusNotify(buildState: 'BUILDING')
                sh 'python3 entrypoint.py'
            }
        }
 

        stage('Unit Tests') {
            steps {
                bitbucketStatusNotify(buildState: 'UNIT TESTING')
                sh 'python3 pipe-unittests.py'
            }
        }
        stage('secp256k1 Tests') {
            steps {
                bitbucketStatusNotify(buildState: 'EC TESTING')
                sh 'python3 pipe-secp256k1tests.py'
            }
        }
        stage('univalue Tests') {
            steps {
                bitbucketStatusNotify(buildState: 'UNIVALUE TESTING')
                sh 'python3 pipe-univaluetests.py'
            }
        }
        stage('leveldb Tests') {
            steps {
                bitbucketStatusNotify(buildState: 'LEVELDB TESTING')
                sh 'python3 pipe-leveldbtests.py'
            }
        }
        stage('Util Tests') {
            steps {
                bitbucketStatusNotify(buildState: 'UTIL TESTING')
                sh 'python3 pipe-utiltests.py'
            }
        }
        stage('Functional Tests') {
            steps {
                bitbucketStatusNotify(buildState: 'FUNCTIONAL TESTING')
                sh 'python3 pipe-functionaltests.py'
            }
        }
    }
    post {
        cleanup { script:  cleanWs() }
        always  { chuckNorris() }
        success {
            bitbucketStatusNotify(buildState: 'SUCCESSFUL')        
            archiveArtifacts 'release-notes.txt , src/bitcoin-cli , src/bitcoin-seeder , src/bitcoin-miner , src/bitcoin-txt , src/bitcoind , build/reports/**'
            junit 'build/reports/*.xml'
        }
        failure {
            bitbucketStatusNotify(buildState: 'FAILED')
            script: emailext (
        to: '$DEFAULT_RECIPIENTS',
                subject: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                body: """<p>FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':</p>
                <p>Check console output (account needed) at &QUOT; \
                  <a href='${env.BUILD_URL}'>${env.JOB_NAME} [${env.BUILD_NUMBER}]</a>&QUOT;</p>""",
                recipientProviders: [[$class: 'CulpritsRecipientProvider'],
                                     [$class: 'DevelopersRecipientProvider'],
                                     [$class: 'RequesterRecipientProvider'], 
                                     [$class: 'FailingTestSuspectsRecipientProvider'],
                                     [$class: 'FirstFailingBuildSuspectsRecipientProvider'],
                                     [$class: 'UpstreamComitterRecipientProvider']]
            )
        }
    }
}
