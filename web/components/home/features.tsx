import { features } from "@/constants/general";

const Features = () => {
  return (
    <div className="app-container ">
      <div className="grid gap-6 mt-14 pb-10">
        <h2 className="text-4xl md:text-4xl text-center font-extrabold">Features</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="grid gap-3 border hover:border-gray border-gray/50 rounded-2xl p-5"
            >
              <feature.icon className="h-8 w-8 text-primary" />
              <h2 className="text-xl md:text-2xl font-bold ">{feature.title}</h2>
              <p className="text-sm md:text-[1rem] text-gray">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Features;
