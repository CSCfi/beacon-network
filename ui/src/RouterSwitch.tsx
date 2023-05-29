import React, {useState} from 'react'
import {Route, Switch, useHistory} from "react-router-dom";
import App from "./App";
import './App.css'

function RouterSwitch() {
    const history = useHistory();

    return <Switch>
            <Route path="/" exact={true} component={App}/>
            <Route path="*" render={() => <>No router match</>}/>
        </Switch>
}

export default RouterSwitch
