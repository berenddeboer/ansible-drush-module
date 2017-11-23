#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: drush

short_description: Manage Drupal sites through drush

version_added: "2.4"

description:
    - This module allows you to manage a site through drush. Requires drush to be in PATH.

options:
    path:
        description:
            - Root if your Drupal site.
        required: true
    command:
        description:
            - Drush command to use.
        required: true
    name:
        description:
            - variable name if using the drush variable-get or variable-set command.
        required: false
    value:
        description:
            - variable value if using the drush variable-set command.
        required: false

author:
    - Berend de Boer (berend@pobox.com)
'''

EXAMPLES = '''
# Check if Drupal website is at the latest version
- name: Get status
  drush: path=/var/www/www.example.com command=core-status
  register: drush

- debug: msg="Latest version"
  when: "drush['drush']['drupal-version'] == '7.56'"

# Get a variable
- name: get variable
  drush: path=/var/www/www.example.com command=variable-get name=cron_safe_threshold
  register: drush

- debug: msg='Cron is disabled'
  when: "drush['cron_safe_threshold'] == 0"

# Set a variable
- name: set variable
  drush: path=/var/www/www.example.com command=variable-set name=page_cache_maximum_age value=3600
  register: drush
'''

RETURN = '''
[ drush | variable_name ]:
    description: drush output in json format.
    type: complex
cmd:
    description: the command-line used to invoke drush. For debugging purposes..
    type: string
rc:
    description: drush exit code.
    type: int
'''

from ansible.module_utils.basic import AnsibleModule
import json

def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        path=dict(type='str', required=True),
        command=dict(type='str', required=True),
        name=dict(type='str', required=False, default=""),
        value=dict(type='str', required=False, default="")
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        rc=0,
        stderr='',
        stdout='',
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    drush = module.get_bin_path('drush', required=True)
    command = module.params['command']
    name = module.params['name']

    # Parameter checking for certain known commands
    if command == 'variable-get':
        if module.params['name'] == '':
            module.fail_json(msg='Variable name required')
    if command == 'variable-set':
        if not module.params['name']:
            module.fail_json(msg='Variable name required')
        if command == 'variable-set' and not module.params['value']:
            module.fail_json(msg='Variable value required')

    # in check-mode for variable-set we report if the variable will be changed
    if command == 'variable-set':
        if module.check_mode:
            command = 'variable-get'
        else:
            # Safe original variable value
            cmd = "%s vget --format=string --exact %s" % (drush, name)
            rc, out, err = module.run_command(cmd, cwd=module.params['path'])
            # ignore errors, most likely variable hasn't been set
            if rc == 0:
                original_value = out.rstrip()
            else:
                original_value = ''
            result['original_value'] = original_value

    # Command could have been changed to a non-destructive one in check-mode.
    # But that's all done, we know the exact command to run, and that all
    # parameters are OK.
    cmd_extra = ''
    if name:
        cmd_extra = cmd_extra + ' ' + name
    if command == 'variable-get' or command == 'variable-set':
        cmd_extra = cmd_extra + ' --exact'

    if command == 'variable-set':
        cmd_extra = cmd_extra + " '" + json.dumps(module.params['value']) + "'"
    else:
        if module.params['value']:
            cmd_extra = cmd_extra + ' ' + module.params['value']

    hates_format = { 'updb', 'updatedb', 'cc', 'cache-clear' }
    if not command in hates_format:
        format = '--format=json'
    else:
        format = ''
    cmd = "%s %s --nocolor -y %s%s" % (drush, command, format, cmd_extra)

    # run drush. In check mode only run drush if it is safe to do so.
    safe_commands = { 'config-get', 'core-requirements', 'core-status', 'drupal-directory', 'pm-info', 'pm-list', 'pm-projectinfo', 'search-status', 'state-get', 'status', 'user-information', 'variable-get', 'watchdog-list', 'watchdog-show' }
    result['cmd'] = cmd
    if not module.check_mode or command in safe_commands:
        rc, out, err = module.run_command(cmd, cwd=module.params['path'])
        result['rc'] = rc
        result['stderr'] = err
        result['stdout'] = out
        # return result as JSON if drush completed succesfully.
        if rc == 0:
            if out == '':
                v = []
            else:
                v = json.loads(out)
            # for variables don't use the generic drush result, but the actual name.
            if command == 'variable-get':
                result[name] = v
                # in check mode report back if we would have changed a variable
                if module.check_mode and module.params['command'] == 'variable-set':
                    result['changed'] = v != module.params['value']
            else:
                if out != '':
                    result['drush'] = v

        # Determine if we have changed anything. In particular for
        # variable-set we're finicky in determining that.
        if not command in safe_commands:
            if command == 'variable-set':
                result['changed'] = original_value != module.params['value']
            else:
                result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if rc != 0:
        module.fail_json(msg=err, **result)

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
