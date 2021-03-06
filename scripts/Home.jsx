import * as React from 'react';
import { UsaStateMap } from './UsaStateMap';
import { Menu } from './Menu';

export function Home() {
  return (
    <div>
      <div id="select-state">
        <h2>State Statistics</h2>
        <Menu />
      </div>
      <img src="static/covid_catcher.png" className="covid-image" alt="covid-catcher" />
      <UsaStateMap />
    </div>
  );
}
