import argparse
import json
import pandas as pd
import vertexai
from vertexai.evaluation import EvalTask
from vertexai.generative_models import GenerativeModel
from vertexai.evaluation.metrics import PointwiseMetric, PointwiseMetricPromptTemplate
import time

def main():
    parser = argparse.ArgumentParser(description="Evaluate an agent.")
    parser.add_argument(
        "--eval_dataset",
        type=str,
        default="agente_ga4/basico.evalset.json",
        help="The path to the evaluation dataset.",
    )
    parser.add_argument(
        "--experiment_name",
        type=str,
        default="ga4-agent-evaluation",
        help="The name of the Vertex AI Experiment.",
    )
    args = parser.parse_args()

    vertexai.init(experiment=args.experiment_name)

    with open(args.eval_dataset, 'r') as f:
        data = json.load(f)
    
    eval_dataset = pd.DataFrame(data['eval_cases'])
    eval_dataset['prompt'] = eval_dataset['conversation'].apply(lambda x: x[0]['user_content']['parts'][0]['text'])
    eval_dataset['reference'] = eval_dataset['conversation'].apply(lambda x: x[0]['final_response']['parts'][0]['text'])
    eval_dataset['predicted_trajectory'] = eval_dataset['conversation'].apply(lambda x: x[0]['intermediate_data']['tool_uses'])

    response_follows_trajectory_prompt_template = PointwiseMetricPromptTemplate(
        criteria={
            "Follows trajectory": (
                "Evaluate whether the agent's response logically follows from the "
                "sequence of actions it took. Consider these sub-points:\n"
                "  - Does the response reflect the information gathered during the trajectory?\n"
                "  - Is the response consistent with the goals and constraints of the task?\n"
                "  - Are there any unexpected or illogical jumps in reasoning?\n"
                "Provide specific examples from the trajectory and response to support your evaluation."
            )
        },
        rating_rubric={
            "1": "Follows trajectory",
            "0": "Does not follow trajectory",
        },
        input_variables=["prompt", "predicted_trajectory"],
    )

    response_follows_trajectory_metric = PointwiseMetric(
        metric="response_follows_trajectory",
        metric_prompt_template=response_follows_trajectory_prompt_template,
    )

    metrics = [
        "exact_match",
        "bleu",
        "rouge_l_sum",
        response_follows_trajectory_metric,
    ]

    eval_task = EvalTask(
        dataset=eval_dataset,
        metrics=metrics,
        experiment=args.experiment_name,
    )

    run_name = f"eval-run-{int(time.time())}"
    eval_result = eval_task.evaluate(
        model=GenerativeModel("gemini-2.5-flash"),
        experiment_run_name=run_name,
    )

    print(eval_result)

if __name__ == "__main__":
    main()