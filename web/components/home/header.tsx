import Button from "../general/button";

const Header = () => {
  return (
    <div className="fixed w-full py-6 backdrop-blur-2xl">
      <div className="app-container flex items-center justify-between">
        <h2 className="text-2xl font-bold">VerifyNG</h2>
        <div className="flex items-center space-x-4">
          <p>How to use</p>
          <p>Features</p>
        </div>

        <Button>Signup</Button>
      </div>
    </div>
  );
};

export default Header;
