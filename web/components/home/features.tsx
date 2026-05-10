import { features } from "@/constants/general";

const Features = () => {
  return (
    <div className="app-container ">
      <div className="grid gap-6 mt-14 pb-10">
        <h2 className="text-3xl md:text-4xl text-center font-bold">Features</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div key={index} className="grid gap-2 border hover:border-gray border-gray/50 rounded-2xl p-4">
              <h2 className="text-xl md:text-2xl font-bold ">{feature.title}</h2>
              <h2 className="text-sm md:text-[1rem]">{feature.description}</h2>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Features;
