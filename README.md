# ansible-drush-module
Allows ansible playbooks to interface with a Drupal site through drush.

Work in progress, but getting web status works, as well as
variable-get and variable-set.

For variable-set we make an effort to determine if the setting is
actually changed (or going to be changed in check mode).


# Examples

```
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

# Modules
- name: disable a module
  drush: path=/var/www/www.example.com command=pm-disable name=devel

- name: enable a module
  drush: path=/var/www/www.example.com command=pm-enable name=memcache
```
