import ResultDetailsClient from "@/components/results/result-details-client";

const ResultDetailsPage = async (props: PageProps<"/results/[job_id]">) => {
  const params = await props.params;

  return <ResultDetailsClient key={params.job_id} jobId={params.job_id} />;
};

export default ResultDetailsPage;
