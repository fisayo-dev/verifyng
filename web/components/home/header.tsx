import Button from "../general/button";

const Header = () => {
  return (
    <div className="fixed w-full py-6 backdrop-blur-2xl">
      <div className="app-container flex items-center justify-between">
        <h2 className="text-2xl font-bold text-primary">VerifyNG</h2>
        <div className="flex items-center space-x-6 justify-center">
          <p>Features</p>
          <p>How to use</p>
        </div>

        <Button>Signup</Button>
      </div>
    </div>
  );
};

export default Header;
