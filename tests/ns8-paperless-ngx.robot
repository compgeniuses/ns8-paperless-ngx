*** Settings ***
Library    SSHLibrary

*** Variables ***
${SCENARIO}    install
${module_id}    ${EMPTY}
${APP_HOST}    paperless.example.org

*** Keywords ***
Paperless responds through Traefik
    ${rc} =    Execute Command    curl --fail --silent --show-error --location --resolve ${APP_HOST}:80:127.0.0.1 http://${APP_HOST}/ -o /dev/null
    ...    return_rc=True    return_stdout=False
    Should Be Equal As Integers    ${rc}    0

*** Test Cases ***
Install Paperless
    IF    '${SCENARIO}' == 'update'
        ${initial_image} =    Set Variable    ghcr.io/compgeniuses/paperlessngx:1.3.1
    ELSE
        ${initial_image} =    Set Variable    ${IMAGE_URL}
    END
    ${output}    ${rc} =    Execute Command    add-module ${initial_image} 1
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}    0
    ${result} =    Evaluate    ast.literal_eval($output)    modules=ast
    Set Suite Variable    ${module_id}    ${result}[module_id]

Configure Paperless
    ${rc} =    Execute Command    api-cli run module/${module_id}/configure-module --data '{"host":"${APP_HOST}","http2https":false,"lets_encrypt":false,"PAPERLESS_ADMIN_PASSWORD":"Test-only-password-123!","PAPERLESS_TIME_ZONE":"UTC"}'
    ...    return_rc=True    return_stdout=False
    Should Be Equal As Integers    ${rc}    0
    Wait Until Keyword Succeeds    5 minutes    10 seconds    Paperless responds through Traefik

Ingest PDF Office and email documents and record original secrets
    Put File    ${CURDIR}/paperless_probe.py    /tmp/paperless-probe-${module_id}.py
    ${output}    ${rc} =    Execute Command    python3 /tmp/paperless-probe-${module_id}.py create /tmp/paperless-proof-${module_id}.json 2>&1
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}    0    ${output}
    Put File    ${CURDIR}/runtime_probe.py    /tmp/paperless-runtime-${module_id}.py
    ${rc} =    Execute Command    python3 /tmp/paperless-runtime-${module_id}.py ${module_id} seed 2>&1
    ...    return_rc=True    return_stdout=False
    Should Be Equal As Integers    ${rc}    0
    ${checksums}    ${rc} =    Execute Command    runagent -m ${module_id} sh -c 'cd "$AGENT_STATE_DIR" && sha256sum database.env secret_key.env'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}    0
    Set Suite Variable    ${original_secrets}    ${checksums}

Upgrade the production baseline
    Skip If    '${SCENARIO}' != 'update'    Fresh install scenario
    ${rc} =    Execute Command    api-cli run update-module --data '{"force":true,"module_url":"ghcr.io/compgeniuses/paperlessngx:1.3.2-testing.1","instances":["${module_id}"]}'
    ...    return_rc=True    return_stdout=False
    Should Be Equal As Integers    ${rc}    0
    Wait Until Keyword Succeeds    5 minutes    10 seconds    Paperless responds through Traefik
    ${output}    ${rc} =    Execute Command    python3 /tmp/paperless-probe-${module_id}.py verify /tmp/paperless-proof-${module_id}.json 2>&1
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}    0    ${output}
    ${rc} =    Execute Command    api-cli run update-module --data '{"force":true,"module_url":"${IMAGE_URL}","instances":["${module_id}"]}'
    ...    return_rc=True    return_stdout=False
    Should Be Equal As Integers    ${rc}    0
    Wait Until Keyword Succeeds    5 minutes    10 seconds    Paperless responds through Traefik

Verify data and secrets after installation or update
    ${output}    ${rc} =    Execute Command    python3 /tmp/paperless-probe-${module_id}.py verify /tmp/paperless-proof-${module_id}.json 2>&1
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}    0    ${output}
    ${checksums}    ${rc} =    Execute Command    runagent -m ${module_id} sh -c 'cd "$AGENT_STATE_DIR" && sha256sum database.env secret_key.env'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}    0
    Should Be Equal    ${checksums}    ${original_secrets}

Verify dependency versions and Redis persistence
    ${output}    ${rc} =    Execute Command    python3 /tmp/paperless-runtime-${module_id}.py ${module_id} verify 2>&1
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}    0    ${output}

Convert new Office and email files after the dependency update
    ${output}    ${rc} =    Execute Command    python3 /tmp/paperless-probe-${module_id}.py create-after /tmp/paperless-after-${module_id}.json 2>&1
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}    0    ${output}

Partial configuration preserves settings and hides secrets
    ${rc} =    Execute Command    api-cli run module/${module_id}/configure-module --data '{"host":"${APP_HOST}","http2https":false,"lets_encrypt":false}'
    ...    return_rc=True    return_stdout=False
    Should Be Equal As Integers    ${rc}    0
    ${output}    ${rc} =    Execute Command    api-cli run module/${module_id}/get-configuration
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}    0
    ${config} =    Evaluate    json.loads($output)    modules=json
    Should Be Equal    ${config}[PAPERLESS_TIME_ZONE]    UTC
    Should Be Empty    ${config}[PAPERLESS_ADMIN_PASSWORD]
    Wait Until Keyword Succeeds    5 minutes    10 seconds    Paperless responds through Traefik

Create a readable PostgreSQL backup
    ${rc} =    Execute Command    runagent -m ${module_id} sh -c 'cd "$AGENT_STATE_DIR" && module-dump-state && pg_dump_file=paperless.pg_dump && test -s "$pg_dump_file" && podman exec -i paperless-pgsql pg_restore --list < "$pg_dump_file" > /dev/null'
    ...    return_rc=True    return_stdout=False
    Should Be Equal As Integers    ${rc}    0

Restore the populated dump into a clean database
    Put File    ${CURDIR}/check_restore_dump.sh    /tmp/paperless-restore-check-${module_id}.sh
    ${output}    ${rc} =    Execute Command    runagent -m ${module_id} bash -s < /tmp/paperless-restore-check-${module_id}.sh
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}    0    ${output}

Restore a full NS8 backup into a clean instance
    Put File    ${CURDIR}/full_restore_probe.py    /tmp/paperless-full-restore-${module_id}.py
    ${output}    ${rc} =    Execute Command    python3 /tmp/paperless-full-restore-${module_id}.py ${module_id} /tmp/paperless-restored.json 2>&1
    ...    return_rc=True
    ${result}    ${found} =    Execute Command    cat /tmp/paperless-restored.json
    ...    return_rc=True
    IF    ${found} == 0
        ${restored} =    Evaluate    json.loads($result)    modules=json
        Set Suite Variable    ${module_id}    ${restored}[module_id]
    END
    Should Be Equal As Integers    ${rc}    0    ${output}
    Wait Until Keyword Succeeds    5 minutes    10 seconds    Paperless responds through Traefik

Uninstall Paperless
    [Teardown]    Close All Connections
    ${rc} =    Execute Command    remove-module --no-preserve ${module_id}
    ...    return_rc=True    return_stdout=False
    Should Be Equal As Integers    ${rc}    0
