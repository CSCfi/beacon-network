import { useState } from "react";
import reactLogo from "./assets/react.svg";
import "./App.css";
import axios from "axios";
import { useCookies } from "react-cookie";

function App() {
  const [cookies, setCookie, removeCookie] = useCookies([
    "logged_in_sub",
    "logged_in_name",
    "logged_in_email",
  ]);

  // general errors messages from everything
  const [error, setError] = useState<string | null>(null);

  const [beaconResult, setBeaconResult] = useState<any[]>([]);
  const [backendResult, setBackendResult] = useState<any>({});

  const makeBeacon = async () => {
    try {
      const { data } = await axios.get("/query");
      setBeaconResult(data);
    } catch (error) {
      setBeaconResult([]);
      if (axios.isAxiosError(error)) {
        setError(error.toString());
      } else {
        setError("Unknown error");
      }
    }
  };

  const makeBackend = async () => {
    try {
      const { data } = await axios.get("/backend-token");
      setBackendResult(data);
    } catch (error) {
      setBackendResult({});
      if (axios.isAxiosError(error)) {
        setError(error.toString());
      } else {
        setError("Unknown error");
      }
    }
  };

  return (
    <div className="App">
      <h1>HGPP Beacon Network (placeholder)</h1>
      <div className="card">
        {cookies.logged_in_sub && (
          <form action="/cilogon/logout" method="POST">
            <button type="submit">Logout</button>
          </form>
        )}
        {!cookies.logged_in_sub && (
          <form action="/cilogon/auth" method="POST">
            <button type="submit">Login via CILogon</button>
          </form>
        )}
      </div>
      <div>{error && <p color="red">{error}</p>}</div>
      <p>
        Sub: {cookies.logged_in_sub && <span>{cookies.logged_in_sub}</span>}
        <br />
        Name: {cookies.logged_in_name && <span>{cookies.logged_in_name}</span>}
        <br />
        Email:{" "}
        {cookies.logged_in_email && <span>{cookies.logged_in_email}</span>}
        <br />
      </p>
      <hr />
      <p className="read-the-docs">
        <button onClick={makeBackend}>Get Backend Token</button>
        <pre>{JSON.stringify(backendResult, null, 2)}</pre>
      </p>
      <hr />
      <p className="read-the-docs">
        <button onClick={makeBeacon}>Make Beacon Query</button>
        <pre>{JSON.stringify(beaconResult, null, 2)}</pre>
      </p>
    </div>
  );
}

export default App;
