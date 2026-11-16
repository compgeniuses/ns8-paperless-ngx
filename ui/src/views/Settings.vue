<template>
  <div class="bx--grid bx--grid--full-width">
    <div class="bx--row">
      <div class="bx--col-lg-16 page-title">
        <h2>{{ $t("settings.title") }}</h2>
      </div>
    </div>
    <div v-if="error.getConfiguration" class="bx--row">
      <div class="bx--col">
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-configuration')"
          :description="error.getConfiguration"
          :showCloseButton="false"
        />
      </div>
    </div>
    <div class="bx--row">
      <div class="bx--col-lg-16">
        <NsTile :light="true">
          <cv-form @submit.prevent="configureModule">
            <NsTextInput
              :label="$t('settings.paperless_fqdn')"
              placeholder="paperless.example.org"
              v-model.trim="host"
              class="mg-bottom"
              :invalid-message="$t(error.host)"
              :disabled="loading.getConfiguration || loading.configureModule"
              ref="host"
            >
            </NsTextInput>
            <NsTextInput
              :label="$t('settings.paperless_admin')"
              placeholder="paperlessadmin"
              v-model="PAPERLESS_ADMIN_USER"
              class="mg-bottom"
              :invalid-message="$t(error.PAPERLESS_ADMIN_USER)"
              :disabled="loading.getConfiguration || loading.configureModule"
              ref="PAPERLESS_ADMIN_USER"
            >
            </NsTextInput>
            <NsTextInput
              :label="$t('settings.paperless_admin_password')"
              :helper-text="$t('settings.password_hint')"
              v-model="PAPERLESS_ADMIN_PASSWORD"
              class="mg-bottom"
              :invalid-message="$t(error.PAPERLESS_ADMIN_PASSWORD)"
              :disabled="loading.getConfiguration || loading.configureModule"
              type="password"
              ref="PAPERLESS_ADMIN_PASSWORD"
            >
            </NsTextInput>
            <NsToggle
              value="letsEncrypt"
              :label="$t('settings.lets_encrypt')"
              v-model="isLetsEncryptEnabled"
              :disabled="loading.getConfiguration || loading.configureModule"
              class="mg-bottom"
            >
              <template slot="text-left">{{
                $t("settings.disabled")
              }}</template>
              <template slot="text-right">{{
                $t("settings.enabled")
              }}</template>
            </NsToggle>
            <NsToggle
              value="httpToHttps"
              :label="$t('settings.http_to_https')"
              v-model="isHttpToHttpsEnabled"
              :disabled="loading.getConfiguration || loading.configureModule"
              class="mg-bottom"
            >
              <template slot="text-left">{{
                $t("settings.disabled")
              }}</template>
              <template slot="text-right">{{
                $t("settings.enabled")
              }}</template>
            </NsToggle>
            <div v-if="error.configureModule" class="bx--row">
              <div class="bx--col">
                <NsInlineNotification
                  kind="error"
                  :title="$t('action.configure-module')"
                  :description="error.configureModule"
                  :showCloseButton="false"
                />
              </div>
            </div>
            <NsProgressBar
              v-if="loading.configureModule"
              :value="configureProgress"
              :indeterminate="!configureProgress"
              class="mg-bottom"
            />
            <NsButton
              kind="primary"
              :icon="Save20"
              :loading="loading.configureModule"
              :disabled="loading.getConfiguration || loading.configureModule"
              >{{ $t("settings.save") }}</NsButton
            >
          </cv-form>
        </NsTile>
      </div>
    </div>
  </div>
</template>

<script>
import to from "await-to-js";
import { mapState } from "vuex";
import {
  QueryParamService,
  UtilService,
  TaskService,
  IconService,
} from "@nethserver/ns8-ui-lib";

export default {
  name: "Settings",
  mixins: [TaskService, IconService, UtilService, QueryParamService],
  pageTitle() {
    return this.$t("settings.title") + " - " + this.appName;
  },
  data() {
    return {
      q: {
        page: "settings",
      },
      urlCheckInterval: null,
      taskEvents: [],
      configureProgress: 0,
      host: "",
      PAPERLESS_ADMIN_USER: "",
      PAPERLESS_ADMIN_PASSWORD: "",
      isLetsEncryptEnabled: false,
      isHttpToHttpsEnabled: false,
      loading: {
        getConfiguration: false,
        configureModule: false,
      },
      error: {
        getConfiguration: "",
        configureModule: "",
        host: "",
        PAPERLESS_ADMIN_USER: "",
        PAPERLESS_ADMIN_PASSWORD: "",
        lets_encrypt: "",
        http2https: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
  },
  created() {
    this.getConfiguration();
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      vm.watchQueryData(vm);
      vm.urlCheckInterval = vm.initUrlBindingForApp(vm, vm.q.page);
    });
  },
  beforeRouteLeave(to, from, next) {
    clearInterval(this.urlCheckInterval);
    next();
  },
  beforeDestroy() {
    for (const [name, callback] of this.taskEvents) {
      this.core.$root.$off(name, callback);
    }
  },
  methods: {
    watchTaskEvent(name, callback, repeated = false) {
      this.taskEvents.push([name, callback]);
      if (repeated) {
        this.core.$root.$on(name, callback);
      } else {
        this.core.$root.$once(name, callback);
      }
    },
    clearTaskEvents(action) {
      this.taskEvents = this.taskEvents.filter(([name, callback]) => {
        if (name.startsWith(action + "-")) {
          this.core.$root.$off(name, callback);
          return false;
        }
        return true;
      });
    },
    configureProgressUpdated(progress) {
      this.configureProgress = progress;
    },
    async getConfiguration() {
      this.loading.getConfiguration = true;
      this.error.getConfiguration = "";
      const taskAction = "get-configuration";
      const eventId = this.getUuid();
      this.watchTaskEvent(
        `${taskAction}-aborted-${eventId}`,
        this.getConfigurationAborted
      );
      this.watchTaskEvent(
        `${taskAction}-completed-${eventId}`,
        this.getConfigurationCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          extra: {
            eventId,
            title: this.$t("action." + taskAction),
            isNotificationHidden: true,
          },
        })
      );
      const err = res[0];

      if (err) {
        this.clearTaskEvents(taskAction);
        console.error(`error creating task ${taskAction}`, err);
        this.error.getConfiguration = this.getErrorMessage(err);
        this.loading.getConfiguration = false;
        return;
      }
    },
    getConfigurationAborted(taskResult, taskContext) {
      this.clearTaskEvents("get-configuration");
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.getConfiguration = this.core.$t("error.generic_error");
      this.loading.getConfiguration = false;
    },
    getConfigurationCompleted(taskContext, taskResult) {
      this.clearTaskEvents("get-configuration");
      const config = taskResult.output;
      this.host = config.host;
      this.PAPERLESS_ADMIN_USER = config.PAPERLESS_ADMIN_USER;
      this.PAPERLESS_ADMIN_PASSWORD = config.PAPERLESS_ADMIN_PASSWORD;
      this.isLetsEncryptEnabled = config.lets_encrypt;
      this.isHttpToHttpsEnabled = config.http2https;
      this.loading.getConfiguration = false;
      this.focusElement("host");
    },
    validateConfigureModule() {
      this.clearErrors(this);

      let isValidationOk = true;

      if (!this.host) {
        this.error.host = "common.required";

        if (isValidationOk) {
          this.focusElement("host");
        }
        isValidationOk = false;
      }
      if (!this.PAPERLESS_ADMIN_USER) {
        this.error.PAPERLESS_ADMIN_USER = "common.required";

        if (isValidationOk) {
          this.focusElement("PAPERLESS_ADMIN_USER");
        }
        isValidationOk = false;
      }

      return isValidationOk;
    },
    configureModuleValidationFailed(validationErrors) {
      this.clearTaskEvents("configure-module");
      this.loading.configureModule = false;
      let focusAlreadySet = false;

      for (const validationError of validationErrors) {
        const param = validationError.parameter;
        // set i18n error message
        this.error[param] = "settings." + validationError.error;

        if (!focusAlreadySet) {
          this.focusElement(param);
          focusAlreadySet = true;
        }
      }
    },
    async configureModule() {
      const isValidationOk = this.validateConfigureModule();
      if (!isValidationOk) {
        return;
      }

      this.loading.configureModule = true;
      const taskAction = "configure-module";
      const eventId = this.getUuid();
      this.watchTaskEvent(
        `${taskAction}-aborted-${eventId}`,
        this.configureModuleAborted
      );
      this.watchTaskEvent(
        `${taskAction}-completed-${eventId}`,
        this.configureModuleCompleted
      );
      this.watchTaskEvent(
        `${taskAction}-validation-failed-${eventId}`,
        this.configureModuleValidationFailed
      );
      this.configureProgress = 0;
      this.watchTaskEvent(
        `${taskAction}-progress-${eventId}`,
        this.configureProgressUpdated,
        true
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: {
            host: this.host,
            PAPERLESS_ADMIN_USER: this.PAPERLESS_ADMIN_USER,
            PAPERLESS_ADMIN_PASSWORD: this.PAPERLESS_ADMIN_PASSWORD,
            lets_encrypt: this.isLetsEncryptEnabled,
            http2https: this.isHttpToHttpsEnabled,
          },
          extra: {
            eventId,
            isProgressNotified: true,
            title: this.$t("settings.instance_configuration", {
              instance: this.instanceName,
            }),
            description: this.$t("settings.configuring"),
          },
        })
      );
      const err = res[0];

      if (err) {
        this.clearTaskEvents(taskAction);
        console.error(`error creating task ${taskAction}`, err);
        this.error.configureModule = this.getErrorMessage(err);
        this.loading.configureModule = false;
        return;
      }
    },
    configureModuleAborted(taskResult, taskContext) {
      this.clearTaskEvents("configure-module");
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.configureModule = this.core.$t("error.generic_error");
      this.loading.configureModule = false;
    },
    configureModuleCompleted() {
      this.clearTaskEvents("configure-module");
      this.loading.configureModule = false;

      // reload configuration
      this.getConfiguration();
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";
.mg-bottom {
  margin-bottom: $spacing-06;
}
</style>
