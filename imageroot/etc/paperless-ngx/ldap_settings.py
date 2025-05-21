# /imageroot/etc/paperless-ngx/ldap_settings.py
import logging
import os
import subprocess
import sys
import ssl

logger = logging.getLogger(__name__)

# Attempt to install django-python3-ldap if requested
__DJANGO_PYTHON3_LDAP_PACKAGE_NAME = "django-python3-ldap"
__HAS_DJANGO_PYTHON3_LDAP = False

try:
    import django_python3_ldap
    __HAS_DJANGO_PYTHON3_LDAP = True
    logger.debug("django-python3-ldap already installed.")
except ModuleNotFoundError:
    logger.debug("django-python3-ldap not initially found.")
    if os.getenv('PAPERLESS_LDAP_PIP_INSTALL', 'false').lower() == "true":
        try:
            logger.info(f"Attempting automatic installation of {__DJANGO_PYTHON3_LDAP_PACKAGE_NAME}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--no-cache-dir", __DJANGO_PYTHON3_LDAP_PACKAGE_NAME],
                check=True,
                capture_output=True, text=True # Capture output for logging
            )
            logger.info(f"{__DJANGO_PYTHON3_LDAP_PACKAGE_NAME} installed successfully.")
            # Need to re-check importability after installation for this run
            import django_python3_ldap
            __HAS_DJANGO_PYTHON3_LDAP = True
        except subprocess.CalledProcessError as e:
            logger.error(f"{__DJANGO_PYTHON3_LDAP_PACKAGE_NAME} installation failed! Error: {e.stderr}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during {__DJANGO_PYTHON3_LDAP_PACKAGE_NAME} installation: {e}")
    else:
        logger.info(f"Not attempting to install {__DJANGO_PYTHON3_LDAP_PACKAGE_NAME} (PAPERLESS_LDAP_PIP_INSTALL not set to 'true').")

# Load default Paperless settings first
from paperless.settings import *

# Conditionally apply LDAP settings if enabled and library is available
PAPERLESS_LDAP_ENABLED = os.getenv('PAPERLESS_LDAP_ENABLED', 'false').lower() == 'true'

if PAPERLESS_LDAP_ENABLED and __HAS_DJANGO_PYTHON3_LDAP:
    logger.info("LDAP authentication is enabled and library is available. Applying LDAP settings.")

    INSTALLED_APPS.append(__DJANGO_PYTHON3_LDAP_PACKAGE_NAME)
    # Ensure LDAPBackend is tried, typically before ModelBackend
    # Common practice is to insert it early, but after any specific permission backends if order matters.
    # Based on mechanarchy's example, inserting at index 2 (after guardian, before ModelBackend if guardian is 0, ModelBackend is 1)
    # Default: AUTHENTICATION_BACKENDS = ["guardian.backends.ObjectPermissionBackend", "django.contrib.auth.backends.ModelBackend"]
    # We want: LDAPBackend, ObjectPermissionBackend, ModelBackend
    # So, insert LDAPBackend at the beginning or adjust based on actual default AUTHENTICATION_BACKENDS
    if "django_python3_ldap.auth.LDAPBackend" not in AUTHENTICATION_BACKENDS:
         AUTHENTICATION_BACKENDS.insert(0, "django_python3_ldap.auth.LDAPBackend")


    # --- Basic LDAP Connection Settings ---
    LDAP_AUTH_URL = os.getenv('PAPERLESS_LDAP_SERVER_URI', '').split(',')
    LDAP_AUTH_CONNECTION_USERNAME = os.getenv('PAPERLESS_LDAP_BIND_DN')
    LDAP_AUTH_CONNECTION_PASSWORD = os.getenv('PAPERLESS_LDAP_BIND_PASSWORD')
    LDAP_AUTH_SEARCH_BASE = os.getenv('PAPERLESS_LDAP_USER_BASE_DN', '') # Required

    # --- TLS Settings ---
    LDAP_AUTH_USE_TLS = os.getenv('PAPERLESS_LDAP_START_TLS', 'false').lower() == 'true'
    _tls_version_str = os.getenv('PAPERLESS_LDAP_TLS_VERSION')
    if _tls_version_str:
        if _tls_version_str.upper() == 'TLSV1.2':
            LDAP_AUTH_TLS_VERSION = ssl.PROTOCOL_TLSv1_2
        elif _tls_version_str.upper() == 'TLSV1.3': # Check if ldap3/python supports this syntax
            LDAP_AUTH_TLS_VERSION = ssl.PROTOCOL_TLSv1_3 if hasattr(ssl, 'PROTOCOL_TLSv1_3') else ssl.PROTOCOL_TLS_CLIENT
        elif _tls_version_str.upper() == 'TLSV1.1': # Older, not recommended
            LDAP_AUTH_TLS_VERSION = ssl.PROTOCOL_TLSv1_1
        elif _tls_version_str.upper() == 'TLSV1': # Older, not recommended
            LDAP_AUTH_TLS_VERSION = ssl.PROTOCOL_TLSv1
        else: # Default to client choosing
            LDAP_AUTH_TLS_VERSION = ssl.PROTOCOL_TLS_CLIENT
            logger.warning(f"Unsupported PAPERLESS_LDAP_TLS_VERSION: {_tls_version_str}. Defaulting to system default.")
    else: # Default if not set
        LDAP_AUTH_TLS_VERSION = ssl.PROTOCOL_TLS_CLIENT


    # --- User Schema & Mapping ---
    LDAP_AUTH_OBJECT_CLASS = os.getenv('PAPERLESS_LDAP_USER_OBJECT_CLASS', 'inetOrgPerson')
    LDAP_AUTH_USER_LOOKUP_FIELDS = (os.getenv('PAPERLESS_LDAP_USER_LOOKUP_FIELD', "username"),)
    LDAP_AUTH_USER_FIELDS = {
        os.getenv('PAPERLESS_LDAP_USER_LOOKUP_FIELD', "username"): os.getenv('PAPERLESS_LDAP_USERNAME_ATTR', "uid"),
        "first_name": os.getenv('PAPERLESS_LDAP_FIRSTNAME_ATTR', "givenName"),
        "last_name": os.getenv('PAPERLESS_LDAP_LASTNAME_ATTR', "sn"),
        "email": os.getenv('PAPERLESS_LDAP_EMAIL_ATTR', "mail"),
    }
    # Ensure the lookup field itself is in LDAP_AUTH_USER_FIELDS mapping
    if LDAP_AUTH_USER_LOOKUP_FIELDS[0] not in LDAP_AUTH_USER_FIELDS:
        LDAP_AUTH_USER_FIELDS[LDAP_AUTH_USER_LOOKUP_FIELDS[0]] = os.getenv('PAPERLESS_LDAP_USERNAME_ATTR', "uid")


    # --- Custom Function Hooks ---
    LDAP_AUTH_SYNC_USER_RELATIONS = "paperless.ldap_settings.custom_sync_user_relations"
    LDAP_AUTH_FORMAT_SEARCH_FILTERS = "paperless.ldap_settings.custom_format_search_filters"
    LDAP_AUTH_FORMAT_USERNAME = "paperless.ldap_settings.custom_format_username" # Renamed from auth_user for clarity

    # --- LLDAP Fix (from mechanarchy) ---
    PAPERLESS_LDAP_LLDAP_FIX = os.getenv('PAPERLESS_LDAP_LLDAP_FIX', 'false').lower() == 'true'
    if PAPERLESS_LDAP_LLDAP_FIX:
        logger.info("Applying LLDAP compatibility fix.")
        try:
            import ldap3
            from django_python3_ldap.utils import format_search_filter as django_format_search_filter

            def hacked_has_user(self, **kwargs):
                self._connection.search(
                    search_base=LDAP_AUTH_SEARCH_BASE,
                    search_filter=django_format_search_filter(kwargs), # Use the one from django_python3_ldap
                    search_scope=ldap3.SUBTREE,
                    attributes=['memberOf', ldap3.ALL_ATTRIBUTES], # Ensure this is a list
                    get_operational_attributes=True,
                    size_limit=1,
                )
                return bool(len(self._connection.response) > 0 and self._connection.response[0].get("attributes"))

            import django_python3_ldap.ldap
            django_python3_ldap.ldap.Connection.has_user = hacked_has_user
            logger.debug("LLDAP fix applied to Connection.has_user.")
        except Exception as e:
            logger.error(f"Failed to apply LLDAP fix: {e}")


    # --- Custom LDAP Functions (adapted from mechanarchy) ---
    def custom_sync_user_relations(user, ldap_attributes, *, connection=None, dn=None):
        logger.debug(f"custom_sync_user_relations called for user {user.username}")
        is_admin = False
        admin_group_dn = os.getenv('PAPERLESS_LDAP_ADMIN_GROUP_DN')
        
        # Determine username attribute from LDAP_AUTH_USER_FIELDS
        username_attr_django = LDAP_AUTH_USER_LOOKUP_FIELDS[0] # e.g. 'username'
        username_attr_ldap = LDAP_AUTH_USER_FIELDS.get(username_attr_django, 'uid') # e.g. 'uid'

        ldap_username = ldap_attributes.get(username_attr_ldap, [user.username])[0]

        if admin_group_dn and 'memberOf' in ldap_attributes:
            if isinstance(ldap_attributes['memberOf'], list):
                if admin_group_dn in ldap_attributes['memberOf']:
                    is_admin = True
            elif isinstance(ldap_attributes['memberOf'], str): # Single group scenario
                if admin_group_dn == ldap_attributes['memberOf']:
                    is_admin = True
        
        if user.is_staff != is_admin or user.is_superuser != is_admin:
            logger.info(f"Updating admin/staff status for user {ldap_username}. Setting is_staff={is_admin}, is_superuser={is_admin}")
            user.is_staff = is_admin
            user.is_superuser = is_admin
            user.save()
        else:
            logger.debug(f"User {ldap_username} admin/staff status already up to date (is_staff={user.is_staff}).")


    def custom_format_search_filters(ldap_fields):
        # Call the base format callable first.
        from django_python3_ldap.utils import format_search_filters as base_format_search_filters
        search_filters = base_format_search_filters(ldap_fields) # ldap_fields is typically {'username': 'actual_username'}

        # Ensure the user is a member of the Paperless LDAP group, if specified
        required_user_group_dn = os.getenv('PAPERLESS_LDAP_REQUIRE_USER_GROUP')
        if required_user_group_dn:
            # This adds an AND condition for memberOf.
            # The format_search_filters already creates a filter like (uid=username)
            # We want (&(uid=username)(memberOf=required_group_dn))
            # So, we modify the ldap_fields that base_format_search_filters uses, or append to its output.
            # format_search_filters expects a dict and creates an AND filter from all items.
            # So, if we add 'memberOf' to ldap_fields, it should be included.
            # However, the library's default format_search_filters might not handle this directly for memberOf.
            # A common way is to append to the list of filters.
            # The library's default creates something like: ['(uid=testuser)']
            # We need to ensure the final filter string is correctly formatted.
            # Let's assume the base filter is the first element.
            
            # Rebuild ldap_fields for base_format_search_filters to include the username attribute correctly
            username_attr_ldap = LDAP_AUTH_USER_FIELDS.get(LDAP_AUTH_USER_LOOKUP_FIELDS[0], "uid")
            current_username = ldap_fields.get(LDAP_AUTH_USER_LOOKUP_FIELDS[0]) # Get the actual username

            # Construct the primary user filter string
            # Example: if username_attr_ldap is 'uid' and current_username is 'testuser', this is '(uid=testuser)'
            user_attr_filter = f"({username_attr_ldap}={current_username})"
            
            # Construct the group membership filter string
            # Example: '(memberOf=cn=paperless_users,ou=groups,dc=example,dc=com)'
            group_membership_filter = f"(memberOf={required_user_group_dn})"
            
            # Combine them into an AND filter
            # Example: '(&(uid=testuser)(memberOf=cn=paperless_users,...))'
            final_filter = f"(&{user_attr_filter}{group_membership_filter})"
            
            search_filters = [final_filter] # Override the default list with our combined filter
            logger.debug(f"Applied required user group. New search filter list: {search_filters}")
            
        return search_filters


    def custom_format_username(model_fields): # Renamed from auth_user for clarity
        # model_fields is a dict like {'username': 'actual_username_entered_at_login'}
        username = model_fields[LDAP_AUTH_USER_LOOKUP_FIELDS[0]]
        user_uid_format = os.getenv('PAPERLESS_LDAP_USER_UID_FORMAT') # E.g., "uid={},ou=people,dc=example,dc=com" or "cn={},ou=users,..."
        
        if user_uid_format:
            formatted_dn = user_uid_format.format(username)
            logger.debug(f"Formatted username for bind/auth as DN: {formatted_dn}")
            return formatted_dn
        else:
            # Fallback if format not specified, though it's generally required for direct bind.
            # django-python3-ldap's default might be just the username, or it might expect a full DN.
            # This part depends heavily on the LDAP server's requirements for binding.
            # For Active Directory, it's often userPrincipalName or sAMAccountName@domain.
            # For OpenLDAP, it's often a full DN.
            logger.warning("PAPERLESS_LDAP_USER_UID_FORMAT not set. Returning raw username for bind, which might fail for some LDAP servers.")
            return username

    # For debugging LDAP settings:
    logger.debug(f"LDAP_AUTH_URL: {LDAP_AUTH_URL}")
    logger.debug(f"LDAP_AUTH_USE_TLS: {LDAP_AUTH_USE_TLS}")
    logger.debug(f"LDAP_AUTH_TLS_VERSION (enum): {LDAP_AUTH_TLS_VERSION if 'LDAP_AUTH_TLS_VERSION' in locals() else 'Not set'}")
    logger.debug(f"LDAP_AUTH_SEARCH_BASE: {LDAP_AUTH_SEARCH_BASE}")
    logger.debug(f"LDAP_AUTH_OBJECT_CLASS: {LDAP_AUTH_OBJECT_CLASS}")
    logger.debug(f"LDAP_AUTH_CONNECTION_USERNAME: {LDAP_AUTH_CONNECTION_USERNAME}")
    # Do NOT log LDAP_AUTH_CONNECTION_PASSWORD
    logger.debug(f"LDAP_AUTH_USER_FIELDS: {LDAP_AUTH_USER_FIELDS}")
    logger.debug(f"LDAP_AUTH_USER_LOOKUP_FIELDS: {LDAP_AUTH_USER_LOOKUP_FIELDS}")
    logger.debug(f"PAPERLESS_LDAP_USER_UID_FORMAT: {os.getenv('PAPERLESS_LDAP_USER_UID_FORMAT')}")
    logger.debug(f"PAPERLESS_LDAP_REQUIRE_USER_GROUP: {os.getenv('PAPERLESS_LDAP_REQUIRE_USER_GROUP')}")
    logger.debug(f"PAPERLESS_LDAP_ADMIN_GROUP_DN: {os.getenv('PAPERLESS_LDAP_ADMIN_GROUP_DN')}")
    logger.debug(f"PAPERLESS_LDAP_LLDAP_FIX: {PAPERLESS_LDAP_LLDAP_FIX}")
    logger.debug(f"AUTHENTICATION_BACKENDS: {AUTHENTICATION_BACKENDS}")

elif PAPERLESS_LDAP_ENABLED and not __HAS_DJANGO_PYTHON3_LDAP:
    logger.error("LDAP authentication is enabled (PAPERLESS_LDAP_ENABLED=true) but the django-python3-ldap library could not be installed or imported. LDAP will not function.")
else:
    logger.info("LDAP authentication is not enabled (PAPERLESS_LDAP_ENABLED is not 'true').")

# Final check on _CHANNELS_REDIS_URL for safety, as mentioned in a GitHub issue.
# This should already be handled by `from paperless.settings import *` if it's set there.
if not hasattr(settings, '_CHANNELS_REDIS_URL') and hasattr(settings, 'PAPERLESS_REDIS'):
    logger.info("Setting _CHANNELS_REDIS_URL from PAPERLESS_REDIS for compatibility.")
    settings._CHANNELS_REDIS_URL = settings.PAPERLESS_REDIS
