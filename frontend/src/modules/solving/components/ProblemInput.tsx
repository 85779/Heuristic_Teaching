import React from "react";

interface ProblemInputProps {
  // Props will be added here
}

export const ProblemInput: React.FC<ProblemInputProps> = (props) => {
  return (
    <div className="problem-input">
      {/* Problem input UI will go here */}
      <input type="text" placeholder="Enter your problem..." />
    </div>
  );
};
