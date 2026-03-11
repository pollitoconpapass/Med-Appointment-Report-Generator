export const StartScreen = ({ language, setLanguage, onStart }) => {
  return (
    <div className="start-screen">
      <div className="language-selector">
        <label>Language:</label>
        <select value={language} onChange={(e) => setLanguage(e.target.value)}>
          <option value="en">English</option>
          <option value="es">Spanish</option>
        </select>
      </div>
      <button className="start-button" onClick={onStart}>
        Start Recording
      </button>
    </div>
  );
};
