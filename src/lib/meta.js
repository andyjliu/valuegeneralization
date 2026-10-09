// Site-level metadata.
export const META = {
  title: 'Predicting Alignment Generalization with Value Representations',
  short: 'Value Generalization',
  paperUrl: 'https://arxiv.org/abs/2610.12410',   // header "Paper" link
  arxivUrl: 'https://arxiv.org/abs/2610.12410',
  codeUrl: 'https://github.com/andyjliu/value-generalization',
  authors: [
    { name: 'Andy Liu', aff: [1] },
    { name: 'Mehar Bhatia', aff: [2, 3] },
    { name: 'Karolina Stańczak', aff: [4, 5] },
    { name: 'Mona Diab', aff: [1] },
    { name: 'Vered Shwartz', aff: [6, 7] },
    { name: 'Daniel Fried', aff: [1] },
  ],
  affiliations: ['Carnegie Mellon University', 'Mila - Quebec AI Institute', 'McGill University', 'ETH Zurich', 'ETH AI Center', 'University of British Columbia', 'Vector Institute'],
  bibtex: `@misc{liu2026predictingalignmentgeneralizationvalue,
      title={Predicting Alignment Generalization with Value Representations},
      author={Andy Liu and Mehar Bhatia and Karolina Stanczak and Mona Diab and Vered Shwartz and Daniel Fried},
      year={2026},
      eprint={2610.12410},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2610.12410},
}`,
};

export const SECTIONS = [
  { id: 'generalization', label: 'Alignment generalization matrices' },
  { id: 'predictors', label: 'Benchmarking predictors' },
  { id: 'taxonomy', label: 'ValueMap Taxonomy' },
  { id: 'multivalue', label: 'Multi-Value Coherence' },
];
