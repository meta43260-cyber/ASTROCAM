/** Stage and Vehicle models */
import { P0, G0 } from './constants.js';

export class Stage {
  constructor({
    name = 'Stage',
    thrustSl = null,   // N
    thrustVac = 0,     // N
    ispSl = null,
    ispVac = 300,
    propMass = 0,
    dryMass = 0,
    burnTime = 100,
    area = 10,
    ignitionDelay = 0,
  }) {
    this.name = name;
    this.thrustSl = thrustSl;
    this.thrustVac = thrustVac;
    this.ispSl = ispSl;
    this.ispVac = ispVac;
    this.propMass = propMass;
    this.dryMass = dryMass;
    this.burnTime = burnTime;
    this.area = area;
    this.ignitionDelay = ignitionDelay;
  }

  thrust(p, burnElapsed = 0) {
    const f = Math.max(0, Math.min(1, p / P0));
    if (this.thrustSl == null) return this.thrustVac;
    return this.thrustVac + (this.thrustSl - this.thrustVac) * f;
  }

  isp(p) {
    if (this.ispSl == null) return this.ispVac;
    const f = Math.max(0, Math.min(1, p / P0));
    return this.ispVac + (this.ispSl - this.ispVac) * f;
  }
}

export class Vehicle {
  constructor({ stages = [], payload = 0, fairingMass = 0, fairingJettisonAlt = 110000 }) {
    this.stages = stages;
    this.payload = payload;
    this.fairingMass = fairingMass;
    this.fairingJettisonAlt = fairingJettisonAlt;
  }

  grossMass() {
    return this.stages.reduce((s, st) => s + st.propMass + st.dryMass, 0)
         + this.payload + this.fairingMass;
  }
}
