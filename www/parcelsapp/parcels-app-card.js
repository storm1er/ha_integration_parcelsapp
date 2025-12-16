import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

class ParcelsAppCard extends LitElement {
  static get properties() {
    return {
      hass: {},
      config: {},
      _trackingId: { state: true },
      _name: { state: true },
    };
  }

  static getConfigElement() {
    return document.createElement("parcels-app-card-editor");
  }

  static getStubConfig() {
    return { title: "Parcels App Packages", max_height: "400px" };
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }
      ha-card {
        color: var(--primary-text-color);
        padding: 12px;
      }
      .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }
      .title {
        font-family: var(--paper-font-headline_-_font-family);
        -webkit-font-smoothing: var(
          --paper-font-headline_-_-webkit-font-smoothing
        );
        font-size: var(--paper-font-headline_-_font-size);
        font-weight: var(--paper-font-headline_-_font-weight);
        letter-spacing: var(--paper-font-headline_-_letter-spacing);
        line-height: var(--paper-font-headline_-_line-height);
        color: var(--primary-text-color);
      }
      .add-package {
        display: flex;
        flex-direction: row;
        gap: 8px;
        margin-bottom: 16px;
      }
      .inputs-column {
        display: flex;
        flex-direction: column;
        flex: 1;
        gap: 8px;
      }
      input {
        width: 100%;
        padding: 10px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 4px;
        background: var(--input-background-color, transparent);
        color: var(--primary-text-color);
        font-size: 1rem;
        box-sizing: border-box;
      }
      input:focus {
        outline: none;
        border-color: var(--primary-color);
      }
      button.add-btn {
        width: 60px;
        background: transparent;
        color: var(--primary-text-color);
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
        padding: 0;
        --mdc-icon-size: 48px;
      }
      button.add-btn:hover {
        color: var(--primary-color);
        transform: scale(1.1);
      }
      .package-list {
        display: flex;
        flex-direction: column;
        gap: 10px;
        overflow-y: auto;
        padding-right: 4px;
      }
      .package-list::-webkit-scrollbar {
        width: 6px;
      }
      .package-list::-webkit-scrollbar-track {
        background: transparent;
      }
      .package-list::-webkit-scrollbar-thumb {
        background-color: var(--scrollbar-thumb-color, rgba(125, 125, 125, 0.3));
        border-radius: 3px;
      }
      .package-item {
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 8px;
        padding: 10px;
        display: flex;
        flex-direction: column;
        gap: 4px;
        transition: box-shadow 0.2s;
      }
      .package-item:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }
      .package-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
      }
      .package-info {
        display: flex;
        flex-direction: column;
      }
      .package-name {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 2px;
      }
      .tracking-id {
        font-size: 0.85rem;
        color: var(--secondary-text-color);
        font-family: monospace;
      }
      .package-status-badge {
        text-transform: uppercase;
        padding: 4px 8px;
        border-radius: 4px;
        background-color: var(--primary-color);
        color: var(--text-primary-color);
        font-size: 0.75rem;
        font-weight: bold;
      }
      .package-status-badge.delivered {
        background-color: var(--success-color, #dbf227);
      }
      .package-status-badge.pending {
        background-color: var(--warning-color, #f2ae33);
      }
      .package-status-badge.unknown {
        background-color: #e23232;
      }
      .package-details {
        font-size: 0.95rem;
        color: var(--primary-text-color);
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: 6px;
        padding: 8px;
        border-radius: 4px;
      }
      .detail-item {
        display: flex;
        flex-direction: column;
      }
      .detail-label {
        font-size: 0.75rem;
        color: var(--secondary-text-color);
        margin-bottom: 1px;
      }
      .detail-value {
        font-weight: 500;
      }
      .message-box {
        margin-top: 2px;
        font-style: italic;
        color: var(--secondary-text-color);
        border-left: 3px solid var(--accent-color);
        padding-left: 8px;
        font-size: 0.9em;
      }
      .actions {
        display: flex;
        justify-content: flex-end;
        margin-top: 2px;
      }
      .delete-btn {
        color: var(--error-color, #db4437);
        background: transparent;
        border: 1px solid var(--error-color, #db4437);
        padding: 6px 12px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.2s;
      }
      .delete-btn:hover {
        background-color: var(--error-color, #db4437);
        color: var(--text-primary-color, white);
      }
      .empty-state {
        text-align: center;
        padding: 24px;
        color: var(--secondary-text-color);
        font-style: italic;
      }
    `;
  }

  setConfig(config) {
    this.config = config;
  }

  getCardSize() {
    if (!this.hass) return 3;
    const count = Object.keys(this.hass.states).filter(
      (eid) =>
        eid.startsWith("sensor.") &&
        this.hass.states[eid].attributes.tracking_id
    ).length;
    return 3 + Math.ceil(count / 2); // Approximation
  }

  render() {
    if (!this.hass) {
      return html``;
    }

    const entities = Object.keys(this.hass.states)
      .filter((eid) => {
        const stateObj = this.hass.states[eid];
        return eid.startsWith("sensor.") && stateObj.attributes.tracking_id;
      })
      .map((eid) => this.hass.states[eid]);

    return html`
      <ha-card>
        <div class="header">
          <div class="title">
            ${(this.config && this.config.title) || "PARCELS APP PACKAGES"}
          </div>
        </div>

        <div class="add-package">
          <div class="inputs-column">
            <input
              type="text"
              placeholder="Tracking ID"
              .value="${this._trackingId || ""}"
              @input="${(e) => (this._trackingId = e.target.value)}"
            />
            <input
              type="text"
              placeholder="Name (Optional)"
              .value="${this._name || ""}"
              @input="${(e) => (this._name = e.target.value)}"
            />
          </div>
          <button class="add-btn" @click="${this._trackPackage}">
            <ha-icon icon="mdi:plus"></ha-icon>
          </button>
        </div>

        <div class="package-list" style="${this.config.max_height ? `max-height: ${this.config.max_height};` : ''}">
          ${entities.length === 0
        ? html`<div class="empty-state">
                No packages currently being tracked. Add one above!
              </div>`
        : entities.map((entity) => this._renderPackage(entity))}
        </div>
      </ha-card>
    `;
  }

  _renderPackage(entity) {
    const attrs = entity.attributes;
    const status = entity.state;
    // Determine status class for coloring
    let statusClass = "";
    const lowerStatus = status.toLowerCase();

    if (["delivered", "pickup"].includes(lowerStatus))
      statusClass = "delivered";
    else if (["pending", "pre_transit"].includes(lowerStatus))
      statusClass = "pending";
    else if (["unknown", "not_found"].includes(lowerStatus))
      statusClass = "unknown";

    // Format last updated: Remove millis and T
    let lastUpdated = attrs.last_updated || "";
    if (lastUpdated) {
      lastUpdated = lastUpdated.split(".")[0].replace("T", " ");
    }

    return html`
      <div class="package-item">
        <div class="package-header">
          <div class="package-info">
            <span class="package-name"
              >${attrs.name || attrs.friendly_name || "Package"}</span
            >
            <span class="tracking-id">${attrs.tracking_id}</span>
          </div>
          <span class="package-status-badge ${statusClass}"
            >${status.replace(/_/g, " ")}</span
          >
        </div>

        <div class="package-details">
          <div class="detail-item">
            <span class="detail-label">Carrier</span>
            <span class="detail-value">${attrs.carrier || "Unknown"}</span>
          </div>
          ${attrs.location && attrs.location !== 'undefined' ? html`
          <div class="detail-item">
            <span class="detail-label">Location</span>
            <span class="detail-value">${attrs.location}</span>
          </div>` : ''}
          ${attrs.days_in_transit !== undefined &&
        attrs.days_in_transit !== null
        ? html` <div class="detail-item">
                <span class="detail-label">Transit Time</span>
                <span class="detail-value">${attrs.days_in_transit} days</span>
              </div>`
        : ""}
          ${lastUpdated
        ? html` <div class="detail-item">
                <span class="detail-label">Last Updated</span>
                <span class="detail-value">${lastUpdated}</span>
              </div>`
        : ""}
          ${attrs.origin
        ? html` <div class="detail-item">
                <span class="detail-label">Origin</span>
                <span class="detail-value">${attrs.origin}</span>
              </div>`
        : ""}
          ${attrs.destination
        ? html` <div class="detail-item">
                <span class="detail-label">Destination</span>
                <span class="detail-value">${attrs.destination}</span>
              </div>`
        : ""}
        </div>

        <div class="message-box">
          "${attrs.message || "No recent status updates"}"
        </div>

        <div class="actions">
          <button
            class="delete-btn"
            @click="${() => this._removePackage(attrs.tracking_id)}"
          >
            Stop Tracking
          </button>
        </div>
      </div>
    `;
  }

  _trackPackage() {
    if (!this._trackingId) {
      alert("Please enter a tracking ID");
      return;
    }

    const serviceData = {
      tracking_id: this._trackingId.trim(),
    };
    if (this._name) {
      serviceData.name = this._name;
    }

    this.hass.callService("parcelsapp", "track_package", serviceData);

    // Clear inputs
    this._trackingId = "";
    this._name = "";
    this.requestUpdate();
  }

  _removePackage(trackingId) {
    if (
      !confirm(
        `Are you sure you want to stop tracking this package: ${trackingId}?`
      )
    )
      return;
    this.hass.callService("parcelsapp", "remove_package", {
      tracking_id: trackingId,
    });
  }
}

class ParcelsAppCardEditor extends LitElement {
  static get properties() {
    return {
      hass: {},
      config: {},
    };
  }

  setConfig(config) {
    this.config = config;
  }

  render() {
    if (!this.hass || !this.config) {
      return html``;
    }

    return html`
      <div class="card-config">
        <div class="option">
          <label class="label">Title</label>
          <input
            type="text"
            .value="${this.config.title || ""}"
            @input="${this._valueChanged}"
            .configValue="${"title"}"
          />
        </div>
        <div class="option">
          <label class="label">Max Height (CSS value, e.g., 400px)</label>
          <input
            type="text"
            .value="${this.config.max_height || ""}"
            @input="${this._valueChanged}"
            .configValue="${"max_height"}"
          />
        </div>
      </div>
    `;
  }

  _valueChanged(ev) {
    if (!this.config || !this.hass) {
      return;
    }
    const target = ev.target;
    if (this[`_${target.configValue}`] === target.value) {
      return;
    }
    if (target.configValue) {
      if (target.value === "") {
        const newConfig = { ...this.config };
        delete newConfig[target.configValue];
        this.config = newConfig;
      } else {
        this.config = {
          ...this.config,
          [target.configValue]: target.value,
        };
      }
    }
    const event = new CustomEvent("config-changed", {
      detail: { config: this.config },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }

  static get styles() {
    return css`
      .card-config {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      .option {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .label {
        font-size: 12px;
        color: var(--secondary-text-color);
        font-weight: 500;
      }
      input {
        padding: 8px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 4px;
        background: var(--input-background-color, transparent);
        color: var(--primary-text-color);
        width: 100%;
        box-sizing: border-box;
      }
      input:focus {
        outline: none;
        border-color: var(--primary-color);
      }
    `;
  }
}

customElements.define("parcels-app-card-editor", ParcelsAppCardEditor);
customElements.define("parcels-app-card", ParcelsAppCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "parcels-app-card",
  name: "Parcels App Tracking Card",
  preview: true,
  description: "Track your packages with ParcelsApp",
});