import { useState } from "react";
import "./App.css";
import axios from "axios";
import { useCookies } from "react-cookie";
import { useQuery } from "react-query";
import { Dna } from "react-loader-spinner";

function App() {
  const [cookies, setCookie, removeCookie] = useCookies([
    "logged_in_sub",
    "logged_in_name",
    "logged_in_email",
    "logged_in_network_beacon_jwt",
  ]);

  // by default the first query should return 0 results and this won't match anything
  const [filter, setFilter] = useState<any | null>({
    id: "GAZ:WONTMATCH",
  });

  // const [backendResult, setBackendResult] = useState<any>({});

  const { data, error, isError, isSuccess, isLoading } = useQuery(
    ["beacon", filter],
    async () => {
      return await axios
        .post(
          "/query",
          {
            meta: {
              apiVersion: "v2.0",
            },
            query: {
              requestedGranularity: "record",
              filters: filter ? [filter] : [],
              pagination: {
                limit: 5000,
                skip: 0,
              },
            },
          },
          {
            headers: {
              Accept: "application/json",
            },
          }
        )
        .then((b) => b.data);
    }
  );

  /*const makeBackend = async () => {
    try {
      const { data } = await axios.get("/backend-token");
      setBackendResult(data);
    } catch (error) {
      setBackendResult({});
      if (axios.isAxiosError(error)) {
        //setError(error.toString());
      } else {
        //setError("Unknown error");
      }
    }
  }; */

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
      <div>
        {isError && <p color="red">{JSON.stringify(error, null, 2)}</p>}
      </div>
      <p>
        Sub: {cookies.logged_in_sub && <span>{cookies.logged_in_sub}</span>}
        <br />
        Name: {cookies.logged_in_name && <span>{cookies.logged_in_name}</span>}
        <br />
        Email:{" "}
        {cookies.logged_in_email && <span>{cookies.logged_in_email}</span>}
        <br />
        Network Beacon JWT:{" "}
        {cookies.logged_in_network_beacon_jwt && (
          <span>{cookies.logged_in_network_beacon_jwt}</span>
        )}
        <br />
      </p>
      <hr />
      {/*<p className="read-the-docs">
        <button onClick={makeBackend}>Get Backend Token</button>
        <pre>{JSON.stringify(backendResult, null, 2)}</pre>
      </p><hr />*/}

      <p className="read-the-docs">
        <button onClick={() => setFilter(null)}>Set Filter to None</button>
        <button onClick={() => setFilter({ id: "GAZ:00002641" })}>
          Set Filter to England
        </button>
        <button onClick={() => setFilter({ id: "GAZ:00002638" })}>
          Set Filter to Northern Island
        </button>
        <pre>{JSON.stringify(filter, null, 2)}</pre>
      </p>
      <hr />
      <p>
        {isLoading && (
          <Dna
            visible={true}
            height="80"
            width="80"
            ariaLabel="dna-loading"
            wrapperStyle={{}}
            wrapperClass="dna-wrapper"
          />
        )}
      </p>
      {isSuccess && (
        <>
          <h5>Summary data returned</h5>
          <pre>
            {JSON.stringify(
              data.map((r: any) => r.responseSummary),
              null,
              2
            )}
          </pre>
          <h5>Record level data returned</h5>
          <pre>
            {JSON.stringify(
              data.map((r: any) =>
                r.response?.resultSets.map((x: any) => x?.resultsCount)
              ),
              null,
              2
            )}
          </pre>
        </>
      )}
    </div>
  );
}

export default App;
