"use strict";

const http = require("http");
const https = require("https");
const { URL } = require("url");

let Service, Characteristic;

module.exports = (api) => {
  Service = api.hap.Service;
  Characteristic = api.hap.Characteristic;
  api.registerAccessory("SleepManagerSwitch", SleepManagerSwitch);
};

/**
 * SleepManagerSwitch — Homebridge accessory for sleep-manager.
 *
 * Maps state machine states to HomeKit:
 *   ON      → Switch.On = true,  StatusFault = NO_FAULT
 *   OFF     → Switch.On = false, StatusFault = NO_FAULT
 *   WAKING  → Switch.On = false, StatusFault = NO_FAULT
 *   FAILED  → Switch.On = false, StatusFault = GENERAL_FAULT
 *
 * Config keys:
 *   name          - Accessory display name
 *   waker_url     - Base URL of the waker (e.g. "http://waker_url:51339")
 *   api_key       - X-API-Key for authentication
 *   poll_interval - Status poll interval in seconds (default: 30)
 */
class SleepManagerSwitch {
  constructor(log, config, api) {
    this.log = log;
    this.name = config.name || "Sleep Manager";
    this.wakerUrl = (config.waker_url || "").replace(/\/$/, "");
    this.apiKey = config.api_key || "";
    this.pollInterval = (config.poll_interval || 30) * 1000;

    if (!this.wakerUrl) {
      this.log.error("homebridge-sleep-manager: waker_url is required in config");
    }

    // Cached state
    this._on = false;
    this._fault = Characteristic.StatusFault.NO_FAULT;

    this._service = new Service.Switch(this.name);

    this._service
      .getCharacteristic(Characteristic.On)
      .onGet(this._getOn.bind(this))
      .onSet(this._setOn.bind(this));

    this._service
      .addCharacteristic(Characteristic.StatusFault)
      .onGet(this._getFault.bind(this));

    // Start polling
    this._pollStatus();
    this._pollTimer = setInterval(this._pollStatus.bind(this), this.pollInterval);
  }

  getServices() {
    return [this._service];
  }

  // -------------------------------------------------------------------------
  // HAP handlers
  // -------------------------------------------------------------------------

  _getOn() {
    return this._on;
  }

  _getFault() {
    return this._fault;
  }

  async _setOn(value) {
    if (value) {
      this.log.info("HomeKit SET on → calling /waker/wake");
      await this._request("GET", "/waker/wake");
    } else {
      this.log.info("HomeKit SET off → calling /waker/suspend");
      await this._request("GET", "/waker/suspend");
    }
    // Optimistic update; next poll will correct if needed
    this._on = value;
  }

  // -------------------------------------------------------------------------
  // Polling
  // -------------------------------------------------------------------------

  async _pollStatus() {
    try {
      const body = await this._request("GET", "/waker/status");
      const data = JSON.parse(body);
      const state = data.state;

      const wasOn = this._on;
      const wasFault = this._fault;

      if (state === "ON") {
        this._on = true;
        this._fault = Characteristic.StatusFault.NO_FAULT;
      } else if (state === "FAILED") {
        this._on = false;
        this._fault = Characteristic.StatusFault.GENERAL_FAULT;
      } else {
        // OFF or WAKING
        this._on = false;
        this._fault = Characteristic.StatusFault.NO_FAULT;
      }

      if (this._on !== wasOn) {
        this._service.getCharacteristic(Characteristic.On).updateValue(this._on);
      }
      if (this._fault !== wasFault) {
        this._service.getCharacteristic(Characteristic.StatusFault).updateValue(this._fault);
      }

      this.log.debug("Polled status: state=%s on=%s fault=%s", state, this._on, this._fault);
    } catch (err) {
      this.log.warn("homebridge-sleep-manager: poll failed —", err.message);
    }
  }

  // -------------------------------------------------------------------------
  // HTTP helper
  // -------------------------------------------------------------------------

  _request(method, path) {
    return new Promise((resolve, reject) => {
      const fullUrl = new URL(path, this.wakerUrl + "/");
      const transport = fullUrl.protocol === "https:" ? https : http;

      const options = {
        hostname: fullUrl.hostname,
        port: fullUrl.port || (fullUrl.protocol === "https:" ? 443 : 80),
        path: fullUrl.pathname + fullUrl.search,
        method,
        headers: {
          "X-API-Key": this.apiKey,
          "Accept": "application/json",
        },
        timeout: 10000,
      };

      const req = transport.request(options, (res) => {
        let raw = "";
        res.on("data", (chunk) => { raw += chunk; });
        res.on("end", () => resolve(raw));
      });

      req.on("timeout", () => { req.destroy(new Error("Request timed out")); });
      req.on("error", reject);
      req.end();
    });
  }
}
