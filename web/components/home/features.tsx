import { features } from "@/constants/general";

const Features = () => {
  return (
    <section id="features" className="app-container scroll-mt-28">
      <div className="grid gap-6 mt-14 pb-10">
        <h2 className="text-4xl md:text-4xl text-center font-extrabold">Features</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="grid gap-3 rounded-2xl border border-gray/40 bg-white p-5 shadow-[0_18px_40px_-28px_rgba(23,23,23,0.28),0_10px_18px_-18px_rgba(0,102,204,0.22)] transition-all duration-300 hover:-translate-y-1 hover:border-primary/20 hover:shadow-[0_26px_55px_-30px_rgba(23,23,23,0.32),0_18px_28px_-22px_rgba(0,102,204,0.28)]"
            >
              <feature.icon className="h-8 w-8 text-primary" />
              <h2 className="text-xl font-bold ">{feature.title}</h2>
              <p className="text-sm  text-gray">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
