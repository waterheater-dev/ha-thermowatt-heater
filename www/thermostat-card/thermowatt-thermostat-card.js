/**
 * Thermowatt Thermostat Card
 * Standalone custom card for Home Assistant Lovelace
 * Based on Home Assistant's default thermostat card
 */

class ThermowattThermostatCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = null;
    this._hass = null;
    this._resizeObserver = null;
    this._containerSize = null;
  }

  static getConfigElement() {
    return document.createElement("hui-card-element-editor");
  }

  static getStubConfig(hass, entities, entitiesFallback) {
    const includeDomains = ["climate", "water_heater"];
    const foundEntities = entities.filter(
      (eid) => includeDomains.includes(eid.split(".")[0])
    );
    return {
      type: "custom:thermowatt-thermostat-card",
      entity: foundEntities[0] || "",
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("You need to define an entity");
    }

    const domain = config.entity.split(".")[0];
    if (!["climate", "water_heater"].includes(domain)) {
      throw new Error(
        "Specify an entity from within the climate or water_heater domain"
      );
    }

    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this._updateCard();
  }

  getCardSize() {
    return 7;
  }

  connectedCallback() {
    this._attachStyles();
    this._createCard();
    this._setupResizeObserver();
  }

  disconnectedCallback() {
    if (this._resizeObserver) {
      this._resizeObserver.disconnect();
    }
  }

  _attachStyles() {
    if (this.shadowRoot.querySelector("style")) {
      return;
    }

    const style = document.createElement("style");
    style.textContent = `
      :host {
        position: relative;
        display: block;
        height: 100%;
      }
      ha-card {
        position: relative;
        height: 100%;
        width: 100%;
        padding: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
      }
      .title {
        width: 100%;
        font-size: var(--ha-font-size-l, 16px);
        line-height: var(--ha-line-height-expanded, 1.5);
        padding: 8px 30px 8px 30px;
        margin: 0;
        text-align: center;
        box-sizing: border-box;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        flex: none;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
      }
      .heating-indicator {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }
      .heating-indicator ha-svg-icon {
        width: 20px;
        height: 20px;
        display: block;
      }
      .heating-indicator.heating ha-svg-icon {
        color: var(--heating-active-color, var(--state-color, var(--primary-color)));
        fill: var(--heating-active-color, var(--state-color, var(--primary-color)));
      }
      .heating-indicator:not(.heating) ha-svg-icon {
        color: var(--disabled-color, rgba(0, 0, 0, 0.38));
        fill: transparent;
        stroke: var(--disabled-color, rgba(0, 0, 0, 0.38));
        stroke-width: 2;
      }
      .container {
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
        max-width: 100%;
        box-sizing: border-box;
        flex: 1;
        min-height: 0;
      }
      .container::before {
        content: "";
        display: block;
        padding-top: 100%;
      }
      .container > * {
        padding: 8px;
      }
      .temperature-control {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .temperature-control ha-state-control-water-heater-temperature,
      .temperature-control ha-state-control-climate-temperature {
        --state-color: var(--state-color, var(--primary-color));
      }
      .more-info {
        position: absolute;
        cursor: pointer;
        top: 0;
        right: 0;
        inset-inline-end: 0px;
        inset-inline-start: initial;
        border-radius: var(--ha-border-radius-pill, 9999px);
        color: var(--secondary-text-color, rgba(0, 0, 0, 0.6));
        direction: var(--direction, ltr);
        z-index: 1;
      }
      .more-info ha-icon-button {
        --mdc-icon-button-size: 40px;
        --mdc-icon-size: 20px;
      }
    `;
    this.shadowRoot.appendChild(style);
  }

  _createCard() {
    if (!this.shadowRoot.querySelector("ha-card")) {
      const card = document.createElement("ha-card");
      this.shadowRoot.appendChild(card);
    }
  }

  _setupResizeObserver() {
    if (!this._resizeObserver && window.ResizeObserver) {
      this._resizeObserver = new ResizeObserver((entries) => {
        const container = this.shadowRoot.querySelector(".container");
        if (container && entries[0]) {
          this._containerSize = entries[0].contentRect.height;
          // Update control size if it exists
          const control = this.shadowRoot.querySelector(
            "ha-state-control-water-heater-temperature, ha-state-control-climate-temperature"
          );
          if (control && this._containerSize) {
            control.style.maxWidth = `${this._containerSize}px`;
          }
        }
      });
      this._resizeObserver.observe(this);
    }
  }

  _updateCard() {
    if (!this._hass || !this._config) {
      return;
    }

    const stateObj = this._hass.states[this._config.entity];
    const card = this.shadowRoot.querySelector("ha-card");

    if (!stateObj) {
      card.innerHTML = `
        <div class="title">Entity not found: ${this._config.entity}</div>
      `;
      return;
    }

    const domain = this._config.entity.split(".")[0];
    const name =
      this._config.name ||
      stateObj.attributes.friendly_name ||
      this._config.entity;

    // Get heating status from attributes (set by the bridge)
    const isHeating = stateObj.attributes.heating === true || 
                     stateObj.attributes.heating === "true" ||
                     (stateObj.attributes.heating !== false && 
                      stateObj.attributes.heating !== "false" && 
                      stateObj.attributes.heating !== null &&
                      stateObj.attributes.heating !== undefined);

    // Create card structure
    card.innerHTML = `
      <div class="title">
        ${this._escapeHtml(name)}
        ${this._createHeatingIndicator(isHeating)}
      </div>
      <div class="container">
        <div class="temperature-control"></div>
      </div>
      <ha-icon-button
        class="more-info"
        .label="${this._hass.localize("ui.card.thermostat.more_info") || "More info"}"
      >
        <ha-svg-icon path="M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,22A2,2 0 0,1 14,24A2,2 0 0,1 12,26A2,2 0 0,1 10,24A2,2 0 0,1 12,22Z"></ha-svg-icon>
      </ha-icon-button>
    `;

    // Compute state color based on operation mode
    // The built-in temperature control components handle colors internally,
    // but we set it here for any custom styling needs
    const stateColor = this._computeStateColor(stateObj, domain);
    
    // Get performance mode color for heating indicator (when heating is active)
    const performanceColor = this._getPerformanceModeColor();
    
    // Apply state color to card and container for potential custom styling
    if (stateColor) {
      card.style.setProperty("--state-color", stateColor);
      const container = card.querySelector(".container");
      if (container) {
        container.style.setProperty("--state-color", stateColor);
      }
    }
    
    // Apply performance color for heating indicator
    if (performanceColor) {
      card.style.setProperty("--heating-active-color", performanceColor);
    }
    
    // Update heating indicator styling
    const heatingIndicator = card.querySelector(".heating-indicator");
    if (heatingIndicator) {
      if (isHeating) {
        heatingIndicator.classList.add("heating");
      } else {
        heatingIndicator.classList.remove("heating");
      }
    }

    // Create and insert temperature control component
    const controlContainer = card.querySelector(".temperature-control");
    if (controlContainer) {
      // Clear any existing control
      controlContainer.innerHTML = "";
      
      const control =
        domain === "water_heater"
          ? this._createWaterHeaterControl(stateObj)
          : this._createClimateControl(stateObj);
      
      controlContainer.appendChild(control);
      
      // Update size if we have container size
      if (this._containerSize) {
        control.style.maxWidth = `${this._containerSize}px`;
      }
      
      // Force update to ensure colors are applied
      // The built-in components handle colors automatically based on stateObj
      setTimeout(() => {
        if (control._updateControl) {
          control._updateControl();
        }
        // Trigger a re-render by updating the stateObj reference
        const updatedStateObj = this._hass.states[this._config.entity];
        if (updatedStateObj && control.stateObj !== updatedStateObj) {
          control.stateObj = updatedStateObj;
        }
      }, 0);
    }

    // Re-attach event listeners
    const moreInfoBtn = card.querySelector(".more-info");
    if (moreInfoBtn) {
      moreInfoBtn.addEventListener("click", () => this._handleMoreInfo());
    }

    // Apply theme if specified
    if (this._config.theme) {
      const themes = this._hass.themes;
      if (themes && themes.themes && themes.themes[this._config.theme]) {
        const theme = themes.themes[this._config.theme];
        // Apply theme variables to the card
        Object.keys(theme).forEach((key) => {
          if (key.startsWith("--")) {
            card.style.setProperty(key, theme[key]);
          }
        });
      }
    }
  }

  _createWaterHeaterControl(stateObj) {
    // Use Home Assistant's built-in water heater control component
    // This component is available in the running HA instance
    const control = document.createElement("ha-state-control-water-heater-temperature");
    
    // Set properties - these components use property setters, not attributes
    control.hass = this._hass;
    control.stateObj = stateObj;
    control.setAttribute("prevent-interaction-on-scroll", "");
    
    // The component will automatically compute and apply colors based on:
    // - stateObj.attributes.operation (operation mode)
    // - stateObj.state (current state)
    // It uses Home Assistant's internal stateColorCss function
    
    // Set max width based on container size
    if (this._containerSize) {
      control.style.maxWidth = `${this._containerSize}px`;
    }

    // Ensure the component updates when hass changes
    const updateControl = () => {
      if (control.hass !== this._hass) {
        control.hass = this._hass;
      }
      if (control.stateObj !== stateObj) {
        control.stateObj = stateObj;
      }
    };
    
    // Store update function for later use
    control._updateControl = updateControl;

    return control;
  }

  _createClimateControl(stateObj) {
    // Use Home Assistant's built-in climate control component
    // This component is available in the running HA instance
    const control = document.createElement("ha-state-control-climate-temperature");
    
    // Set properties - these components use property setters, not attributes
    control.hass = this._hass;
    control.stateObj = stateObj;
    control.setAttribute("prevent-interaction-on-scroll", "");
    
    // The component will automatically compute and apply colors based on:
    // - stateObj.attributes.hvac_action (heating/cooling/idle)
    // - stateObj.state (hvac mode)
    // It uses Home Assistant's internal stateColorCss function
    
    // Set max width based on container size
    if (this._containerSize) {
      control.style.maxWidth = `${this._containerSize}px`;
    }

    // Ensure the component updates when hass changes
    const updateControl = () => {
      if (control.hass !== this._hass) {
        control.hass = this._hass;
      }
      if (control.stateObj !== stateObj) {
        control.stateObj = stateObj;
      }
    };
    
    // Store update function for later use
    control._updateControl = updateControl;

    return control;
  }

  _handleMoreInfo() {
    const event = new CustomEvent("hass-more-info", {
      bubbles: true,
      composed: true,
      detail: {
        entityId: this._config.entity,
      },
    });
    this.dispatchEvent(event);
  }

  _escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  _createHeatingIndicator(isHeating) {
    // Material Design Icons: mdi-fire
    // Fire icon path - we'll style it as filled or outline via CSS
    const firePath = "M17.66 11.2C17.43 10.9 17.15 10.64 16.89 10.38C16.22 9.78 15.46 9.35 14.82 8.72C13.33 7.26 13 4.85 13.95 3C15.98 4.79 16.34 7.35 15.97 9.03C15.77 9.9 15.5 10.67 15.24 11.5C15.18 11.72 15.12 11.94 15.07 12.17L14.5 14.85C14.37 15.5 14.24 16.15 14.12 16.79L13.75 19.25C13.6 20.09 13.43 20.92 13.28 21.75C13.15 22.4 13 23.05 12.85 23.7L12.5 25.5H11.5L11.14 23.7C10.99 23.05 10.84 22.4 10.71 21.75C10.56 20.92 10.39 20.09 10.24 19.25L9.87 16.79C9.75 16.15 9.62 15.5 9.5 14.85L8.93 12.17C8.88 11.94 8.82 11.72 8.76 11.5C8.5 10.67 8.23 9.9 8.03 9.03C7.66 7.35 8.02 4.79 10.05 3C11 4.85 10.67 7.26 9.18 8.72C8.54 9.35 7.78 9.78 7.11 10.38C6.85 10.64 6.57 10.9 6.34 11.2C5.67 11.95 5 12.7 4.5 13.5C4.05 14.25 3.75 15.08 3.5 15.9C3.25 16.7 3.1 17.5 3 18.25C2.9 19 2.85 19.75 2.85 20.5C2.85 21.25 2.9 22 3 22.75C3.1 23.5 3.25 24.3 3.5 25.1C3.75 25.92 4.05 26.75 4.5 27.5C5 28.3 5.67 29.05 6.34 29.8C6.57 30.1 6.85 30.36 7.11 30.62C7.78 31.22 8.54 31.65 9.18 32.28C10.67 33.74 11 36.15 10.05 38C8.02 36.21 7.66 33.65 8.03 31.97C8.23 31.1 8.5 30.33 8.76 29.5C8.82 29.28 8.88 29.06 8.93 28.83L9.5 26.15C9.62 25.5 9.75 24.85 9.87 24.21L10.24 21.75C10.39 20.91 10.56 20.08 10.71 19.25C10.84 18.6 10.99 17.95 11.14 17.3L11.5 15.5H12.5L12.85 17.3C13 17.95 13.15 18.6 13.28 19.25C13.43 20.08 13.6 20.91 13.75 21.75L14.12 24.21C14.24 24.85 14.37 25.5 14.5 26.15L15.07 28.83C15.12 29.06 15.18 29.28 15.24 29.5C15.5 30.33 15.77 31.1 15.97 31.97C16.34 33.65 15.98 36.21 13.95 38C13 36.15 13.33 33.74 14.82 32.28C15.46 31.65 16.22 31.22 16.89 30.62C17.15 30.36 17.43 30.1 17.66 29.8C18.33 29.05 19 28.3 19.5 27.5C19.95 26.75 20.25 25.92 20.5 25.1C20.75 24.3 20.9 23.5 21 22.75C21.1 22 21.15 21.25 21.15 20.5C21.15 19.75 21.1 19 21 18.25C20.9 17.5 20.75 16.7 20.5 15.9C20.25 15.08 19.95 14.25 19.5 13.5C19 12.7 18.33 11.95 17.66 11.2M12.5 7C13.88 7 15 8.12 15 9.5C15 10.88 13.88 12 12.5 12C11.12 12 10 10.88 10 9.5C10 8.12 11.12 7 12.5 7M12.5 13C14.43 13 16 14.57 16 16.5C16 18.43 14.43 20 12.5 20C10.57 20 9 18.43 9 16.5C9 14.57 10.57 13 12.5 13Z";
    
    return `
      <span class="heating-indicator ${isHeating ? 'heating' : ''}" title="${isHeating ? 'Heating Active' : 'Heating Off'}">
        <ha-svg-icon path="${firePath}"></ha-svg-icon>
      </span>
    `;
  }

  _getPerformanceModeColor() {
    // Get the color used for performance mode (same as manual mode in our color map)
    const root = document.documentElement;
    const computedStyle = getComputedStyle(root);
    
    // Try to get performance/manual mode color
    const color = computedStyle.getPropertyValue("--state-water-heater-performance-color")?.trim() ||
                  computedStyle.getPropertyValue("--state-water-heater-active-color")?.trim() ||
                  computedStyle.getPropertyValue("--orange-color")?.trim() ||
                  computedStyle.getPropertyValue("--primary-color")?.trim();
    
    return color || null;
  }

  _computeStateColor(stateObj, domain) {
    // Try to use Home Assistant's state color computation if available
    // The hass object might have utility functions
    if (this._hass && this._hass.callService && window.stateColorCss) {
      try {
        return window.stateColorCss(stateObj);
      } catch (e) {
        // Fall through to manual computation
      }
    }

    // Get computed style to access CSS variables
    const root = document.documentElement;
    const computedStyle = getComputedStyle(root);
    
    // Check if entity is active (not off/unavailable)
    const state = stateObj.state;
    if (state === "unavailable" || state === "unknown") {
      return null; // Let components handle unavailable state
    }

    if (domain === "water_heater") {
      const operation = (stateObj.attributes.operation || state).toLowerCase();
      
      // Map water heater operation modes to CSS variable names
      // These should match Home Assistant's internal state color system
      const colorMap = {
        "eco": "--state-water-heater-eco-color",
        "holiday": "--state-water-heater-electric-color", 
        "manual": "--state-water-heater-performance-color",
         "auto": "--state-water-heater-heat-pump-color",
        "manual": "--state-water-heater-active-color",
        "off": null // Off uses disabled color, handled by components
      };
      
      const colorVar = colorMap[operation];
      if (colorVar) {
        const color = computedStyle.getPropertyValue(colorVar)?.trim();
        if (color) {
          return color;
        }
      }
      
      // Fallback: use primary color for active modes (not off)
      if (operation !== "off") {
        return computedStyle.getPropertyValue("--primary-color")?.trim() || null;
      }
    } else if (domain === "climate") {
      const hvacMode = stateObj.state;
      const hvacAction = stateObj.attributes.hvac_action;
      
      // Use action if available, otherwise use mode
      const activeState = hvacAction && hvacAction !== "idle" ? hvacAction : hvacMode;
      
      const colorMap = {
        "heating": "--state-climate-heating-color",
        "cooling": "--state-climate-cooling-color",
        "heat_cool": "--state-climate-auto-color",
        "auto": "--state-climate-auto-color",
        "off": null,
        "idle": null
      };
      
      const colorVar = colorMap[activeState];
      if (colorVar) {
        const color = computedStyle.getPropertyValue(colorVar)?.trim();
        if (color) {
          return color;
        }
      }
      
      // Fallback for active climate states
      if (activeState !== "off" && activeState !== "idle") {
        return computedStyle.getPropertyValue("--primary-color")?.trim() || null;
      }
    }
    
    return null; // Let components handle default colors
  }
}

customElements.define("thermowatt-thermostat-card", ThermowattThermostatCard);
