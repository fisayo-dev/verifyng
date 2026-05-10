import { ReactNode } from "react";

const Button = ({ children }: { children: ReactNode }) => {
  return (
    <button className="bg-primary px-5 py-3 rounded-full text-white hover:bg-primary/80 hover:cursor-pointer hover:scale-110 transition-all">
      {children}
    </button>
  );
};

export default Button;
