import Header from "@/components/home/header";
import { ReactNode } from "react";

const HomeLayout = ({ children }: { children: ReactNode }) => {
  return (
    <div>
      <Header />
      <div className="mt-20">{children}</div>
    </div>
  );
};

export default HomeLayout;
