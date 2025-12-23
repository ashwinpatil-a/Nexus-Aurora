import { auth } from './firebase'; // Import the file we just made

function App() {
  // Add this log
  console.log("🔥 Firebase Connected:", auth); 

  return (
    <div className="App">
       <h1>Nexus Setup Check</h1>
    </div>
  );
}

export default App;