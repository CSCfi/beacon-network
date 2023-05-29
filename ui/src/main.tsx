import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import RouterSwitch from "./RouterSwitch";
import {BrowserRouter} from "react-router-dom";

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
    <React.StrictMode>
        <BrowserRouter>
            <RouterSwitch/>
        </BrowserRouter>
    </React.StrictMode>,
)
