import { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
}

const Button = ({ children, className = "", ...props }: ButtonProps) => {
  return (
    <button
      className={`rounded-full bg-primary px-5 py-3 text-white transition-all hover:cursor-pointer hover:scale-110 hover:bg-primary/80 disabled:hover:cursor-not-allowed disabled:hover:scale-100 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
